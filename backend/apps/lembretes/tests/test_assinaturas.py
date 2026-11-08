"""[010] Assinaturas de push: guardar, repetir, trocar de dono, lista de serviços (SSRF), chaves, limite, remover, autoria."""

import pytest
import requests

from apps.lembretes.models import AssinaturaPush

from .conftest import FCM, assinar, assinatura, b64url, desassinar


@pytest.fixture(autouse=True)
def sem_rede(monkeypatch):
    """Nenhuma assinatura pode fazer o servidor chamar o endereço dela (ABU-21): qualquer chamada de rede falha o teste."""

    def proibido(*args, **kwargs):
        raise AssertionError("o servidor tentou chamar o endereço da assinatura")

    monkeypatch.setattr(requests.sessions.Session, "send", proibido)
    monkeypatch.setattr("socket.getaddrinfo", proibido)


def test_req_18_3_guarda_a_assinatura_do_participante(dono):
    """[010] REQ-18.3: 201 e a assinatura fica com a pessoa."""
    resposta = assinar(dono)

    assert resposta.status_code == 201, resposta.content
    guardada = AssinaturaPush.objects.get()
    assert guardada.endpoint == FCM
    assert guardada.usuario.email == "dono@example.com"


def test_req_18_3_reenviar_a_mesma_assinatura_nao_duplica(dono):
    """[010] REQ-18.3."""
    assert assinar(dono).status_code == 201
    assert assinar(dono).status_code == 201

    assert AssinaturaPush.objects.count() == 1


def test_req_18_3_assinatura_de_outra_conta_passa_para_a_conta_atual(par):
    """[010] REQ-18.3: o mesmo navegador entrando com outra conta."""
    dono, parceiro = par
    assinar(dono)

    assert assinar(parceiro).status_code == 201

    assert AssinaturaPush.objects.get().usuario.email == "par@example.com"


@pytest.fixture
def par(dono, parceiro):
    return dono, parceiro()


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://fcm.googleapis.com/fcm/send/x",  # sem HTTPS
        "https://localhost/push",
        "https://127.0.0.1/push",
        "https://[::1]/push",
        "https://10.0.0.5/push",
        "https://192.168.0.10/push",
        "https://169.254.169.254/latest/meta-data",
        "https://metadata.google.internal/",
        "https://evil.example.com/fcm.googleapis.com",
        "https://fcm.googleapis.com.evil.com/send/x",
        "https://evilpush.apple.com/send/x",
        "https://evilnotify.windows.com/send/x",
        "https://push.apple.com/send/x",
        "https://evilfcm.googleapis.com/send/x",
        "https://fcm.googleapis.com@evil.com/send/x",
        "https://user:senha@fcm.googleapis.com/send/x",
        "https://fcm.googleapis.com:8443/send/x",
        "https://fcm.googleapis.com./send/x",
        "ftp://fcm.googleapis.com/x",
        "file:///etc/passwd",
        "//fcm.googleapis.com/send/x",
        "fcm.googleapis.com/send/x",
        "https://fcm.googleapis.com/" + "a" * 3000,
        "",
        "   ",
    ],
)
def test_req_18_4_abu_21_endereco_fora_da_lista_da_422_sem_chamar_o_endereco(dono, endpoint):
    """[010] REQ-18.4 / ABU-21 / CTL-81: nenhum endereço fora da lista é aceito nem chamado."""
    resposta = assinar(dono, endpoint)

    assert resposta.status_code == 422, endpoint
    assert AssinaturaPush.objects.count() == 0


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://fcm.googleapis.com/fcm/send/abc",
        "https://updates.push.services.mozilla.com/wpush/v2/abc",
        "https://web.push.apple.com/abc",
        "https://api.push.apple.com/3/device/abc",
        "https://wns2-par02p.notify.windows.com/w/?token=abc",
    ],
)
def test_req_18_4_servicos_de_push_conhecidos_sao_aceitos(dono, endpoint):
    """[010] REQ-18.4: a lista fixa."""
    assert assinar(dono, endpoint).status_code == 201


@pytest.mark.parametrize(
    "corpo",
    [
        {},
        {"endpoint": FCM},
        {"endpoint": FCM, "keys": {}},
        {"endpoint": FCM, "keys": {"p256dh": "x"}},
        {"endpoint": FCM, "keys": "texto"},
        {"endpoint": 5, "keys": {"p256dh": "a", "auth": "b"}},
        {"endpoint": None, "keys": None},
        [],
    ],
)
def test_req_18_4_corpo_mal_formado_da_422(dono, corpo):
    """[010] REQ-18.4 / NFR-LEMB-5."""
    resposta = dono.postar("/api/v1/lembretes/assinaturas", corpo)

    assert resposta.status_code == 422
    assert AssinaturaPush.objects.count() == 0


@pytest.mark.parametrize(
    "chaves",
    [
        {"p256dh": "isto não é base64 !!!"},
        {"p256dh": b64url(b"curto")},
        {"p256dh": b64url(b"\x03" + bytes(64))},  # não começa com 0x04
        {"auth": b64url(b"curto")},
        {"auth": b64url(bytes(40))},
        {"auth": 7},
        {"p256dh": ""},
    ],
)
def test_req_18_4_chaves_invalidas_dao_422(dono, chaves):
    """[010] REQ-18.4: p256dh = 65 bytes de ponto não comprimido; auth = 16 bytes."""
    resposta = dono.postar("/api/v1/lembretes/assinaturas", assinatura(**chaves))

    assert resposta.status_code == 422
    assert AssinaturaPush.objects.count() == 0


def test_req_18_5_sexta_assinatura_da_409(dono):
    """[010] REQ-18.5."""
    for i in range(5):
        assert assinar(dono, f"https://fcm.googleapis.com/fcm/send/{i}").status_code == 201

    resposta = assinar(dono, "https://fcm.googleapis.com/fcm/send/6")

    assert resposta.status_code == 409
    assert AssinaturaPush.objects.count() == 5
    # reenviar uma que já existe continua valendo, mesmo com 5
    assert assinar(dono, "https://fcm.googleapis.com/fcm/send/0").status_code == 201


def test_req_18_6_desligar_remove_a_assinatura_do_aparelho(dono):
    """[010] REQ-18.6."""
    assinar(dono)
    assinar(dono, "https://fcm.googleapis.com/fcm/send/outro")

    resposta = desassinar(dono)

    assert resposta.status_code == 204
    assert [a.endpoint for a in AssinaturaPush.objects.all()] == [
        "https://fcm.googleapis.com/fcm/send/outro"
    ]


def test_abu_22_ninguem_remove_a_assinatura_de_outra_pessoa(par):
    """[010] ABU-22: 404 e nada muda."""
    dono, parceiro = par
    assinar(dono)

    resposta = desassinar(parceiro)

    assert resposta.status_code == 404
    assert AssinaturaPush.objects.count() == 1


def test_abu_22_remover_o_que_nao_existe_da_404(dono):
    """[010] ABU-22."""
    assert desassinar(dono).status_code == 404


def test_req_18_3_sem_sessao_da_401(cliente):
    """[010] REQ-18.3: anônimo não faz nada com lembretes."""
    assert cliente.postar("/api/v1/lembretes/assinaturas", assinatura()).status_code in (401, 403)
    assert cliente.get("/api/v1/lembretes/chave-publica").status_code in (401, 403)


def test_req_18_2_a_chave_publica_sai_pela_api_e_a_privada_nunca(dono, settings):
    """[010] REQ-18.2 / NFR-LEMB-1 / CTL-82: só a pública."""
    settings.VAPID_PUBLIC_KEY = "CHAVE-PUBLICA-DE-TESTE"
    settings.VAPID_PRIVATE_KEY = "CHAVE-PRIVADA-SECRETA-NAO-PODE-SAIR"

    resposta = dono.get("/api/v1/lembretes/chave-publica")

    assert resposta.status_code == 200
    assert resposta.json() == {"chave": "CHAVE-PUBLICA-DE-TESTE"}
    assert "SECRETA" not in resposta.content.decode()


def test_req_18_2_sem_chave_configurada_a_rota_diz_que_nao_ha_lembretes(dono, settings):
    """[010] REQ-18.7: sem VAPID o app esconde a seção (503)."""
    settings.VAPID_PUBLIC_KEY = ""

    resposta = dono.get("/api/v1/lembretes/chave-publica")

    assert resposta.status_code == 503
