"""[010] O envio real (com o `webpush` falso), os comandos e o segredo VAPID."""

import io
import logging
from types import SimpleNamespace

import pytest
import requests
from django.core.management import call_command
from py_vapid import Vapid
from pywebpush import WebPushException

from apps.lembretes import envio as modulo_envio
from apps.lembretes.models import AssinaturaPush, LembreteEnviado

from .conftest import FCM

PRIVADA = "CHAVE-PRIVADA-SECRETA-NAO-PODE-SAIR-NEM-NO-LOG"


@pytest.fixture
def configurado(settings):
    settings.VAPID_PRIVATE_KEY = PRIVADA
    settings.VAPID_PUBLIC_KEY = "publica"
    settings.VAPID_ASSUNTO = "mailto:dono@example.com"


@pytest.fixture
def assinatura_guardada(pessoas):
    pessoas("ana", n_assinaturas=0)
    from django.contrib.auth import get_user_model

    return AssinaturaPush.objects.create(
        usuario=get_user_model().objects.get(email="ana@example.com"),
        endpoint=FCM,
        p256dh="PP",
        auth="AA",
    )


def resposta_http(status):
    return SimpleNamespace(status_code=status)


def test_req_19_1_envio_usa_vapid_timeout_e_a_carga(configurado, assinatura_guardada, monkeypatch):
    """[010] REQ-19.1 / NFR-LEMB-1: chama o `webpush` com a chave do ambiente, assunto e tempo limite."""
    chamado = {}

    def falso(**kwargs):
        chamado.update(kwargs)

    monkeypatch.setattr(modulo_envio, "webpush", falso)

    resultado = modulo_envio.enviar_web_push(assinatura_guardada, '{"corpo":"x"}')

    assert resultado == "ok"
    assert chamado["subscription_info"] == {"endpoint": FCM, "keys": {"p256dh": "PP", "auth": "AA"}}
    assert chamado["data"] == '{"corpo":"x"}'
    assert chamado["vapid_private_key"] == PRIVADA
    assert chamado["vapid_claims"] == {"sub": "mailto:dono@example.com"}
    assert 0 < chamado["timeout"] <= 15


@pytest.mark.parametrize(
    "status,esperado",
    [(404, "gone"), (410, "gone"), (500, "falha"), (429, "falha"), (400, "falha")],
)
def test_req_19_4_19_8_status_do_servico_de_push(
    configurado, assinatura_guardada, monkeypatch, status, esperado
):
    """[010] REQ-19.4 / REQ-19.8: 404 e 410 = assinatura morta; o resto = falha."""

    def falso(**kwargs):
        raise WebPushException("erro", response=resposta_http(status))

    monkeypatch.setattr(modulo_envio, "webpush", falso)

    assert modulo_envio.enviar_web_push(assinatura_guardada, "{}") == esperado


def test_req_19_8_falha_de_rede_e_falha_comum(configurado, assinatura_guardada, monkeypatch):
    """[010] REQ-19.8."""

    def falso(**kwargs):
        raise requests.ConnectionError("sem rede")

    monkeypatch.setattr(modulo_envio, "webpush", falso)

    assert modulo_envio.enviar_web_push(assinatura_guardada, "{}") == "falha"


def test_abu_21_endereco_adulterado_no_banco_nao_e_chamado_nem_no_envio(
    configurado, assinatura_guardada, monkeypatch
):
    """[010] ABU-21 / CTL-81: defesa em profundidade, a lista vale também na hora de enviar."""
    AssinaturaPush.objects.filter(pk=assinatura_guardada.pk).update(
        endpoint="https://169.254.169.254/x"
    )
    assinatura_guardada.refresh_from_db()
    monkeypatch.setattr(
        modulo_envio, "webpush", lambda **kw: pytest.fail("chamou o endereço interno")
    )

    assert modulo_envio.enviar_web_push(assinatura_guardada, "{}") == "falha"


def test_nfr_lemb_1_a_chave_privada_nao_vai_ao_log_nem_nas_mensagens_de_erro(
    configurado, assinatura_guardada, monkeypatch, caplog
):
    """[010] NFR-LEMB-1 / CTL-82."""

    def falso(**kwargs):
        raise WebPushException(
            f"falha com {kwargs['vapid_private_key']}", response=resposta_http(500)
        )

    monkeypatch.setattr(modulo_envio, "webpush", falso)

    with caplog.at_level(logging.DEBUG):
        modulo_envio.enviar_web_push(assinatura_guardada, "{}")

    assert "SECRETA" not in "\n".join(r.getMessage() for r in caplog.records)


def test_comando_enviar_lembretes_executa_uma_vez_na_hora_dada(pessoas, monkeypatch):
    """[010] T-2.3: `enviar_lembretes --agora ISO` roda o disparador uma vez."""
    pessoas("ana")
    enviados = []
    monkeypatch.setattr(
        "apps.lembretes.management.commands.enviar_lembretes.enviar_web_push",
        lambda assinatura, carga: enviados.append(assinatura.usuario_id) or "ok",
    )
    saida = io.StringIO()

    call_command("enviar_lembretes", "--agora", "2026-11-05T21:30:00-03:00", stdout=saida)

    assert len(enviados) == 1
    assert "enviados=1" in saida.getvalue()
    assert LembreteEnviado.objects.count() == 1


def test_comando_enviar_lembretes_recusa_data_sem_fuso(db):
    """[010] T-2.3: sem fuso a hora seria ambígua."""
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("enviar_lembretes", "--agora", "2026-11-05T21:30:00")


def test_comando_rodar_lembretes_marca_o_batimento_a_cada_ciclo(
    settings, tmp_path, monkeypatch, pessoas
):
    """[010] NFR-LEMB-3: arquivo de batimento atualizado a cada tick (a saúde do contêiner lê a idade dele)."""
    settings.LEMBRETES_BATIMENTO = tmp_path / "batimento"
    monkeypatch.setattr(
        "apps.lembretes.management.commands.rodar_lembretes.enviar_web_push", lambda a, c: "ok"
    )

    call_command("rodar_lembretes", "--ciclos", "2", "--intervalo", "0")

    assert (tmp_path / "batimento").exists()


def test_gerar_vapid_imprime_um_par_que_funciona_e_nao_grava_nada(db, tmp_path):
    """[010] T-2.3 / NFR-LEMB-1: o par impresso assina de verdade e a pública bate com a privada."""
    saida = io.StringIO()

    call_command("gerar_vapid", stdout=saida)

    linhas = dict(linha.split("=", 1) for linha in saida.getvalue().splitlines() if "=" in linha)
    publica, privada = linhas["VAPID_PUBLIC_KEY"], linhas["VAPID_PRIVATE_KEY"]
    chave = Vapid.from_string(privada)
    assinado = chave.sign(
        {"aud": "https://fcm.googleapis.com", "sub": "mailto:a@b.c", "exp": 9999999999}
    )
    assert "Authorization" in assinado or "authorization" in {k.lower() for k in assinado}
    from cryptography.hazmat.primitives import serialization

    bruto = chave.public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    import base64

    assert base64.urlsafe_b64encode(bruto).rstrip(b"=").decode() == publica
    assert len(publica) == 87
