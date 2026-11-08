"""[011] Recuperação de senha por e-mail: pedido (resposta uniforme, limite, link, segundo plano) e redefinição (token)."""

import logging
import re
import time
from datetime import datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.acesso import recuperacao
from apps.acesso.models import PedidoRecuperacao

from .conftest import SENHA, Cliente

SENHA_NOVA = "uma-senha-nova-bem-comprida-91"
MENSAGEM = "Se este e-mail tiver conta, enviamos um link. Vale por 1 hora."
URL = "/api/v1/auth/recuperacao"
URL_REDEFINIR = "/api/v1/auth/redefinir"
BASE = "https://app.exemplo.org/entrelinhas/"


@pytest.fixture(autouse=True)
def ambiente(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.APP_URL_BASE = BASE
    settings.DEFAULT_FROM_EMAIL = "Entrelinhas <nao-responda@exemplo.org>"
    settings.EMAIL_HOST_PASSWORD = "SENHA-SMTP-SECRETA-NAO-PODE-SAIR"
    mail.outbox.clear()
    yield
    recuperacao.aguardar_envios()


@pytest.fixture
def ana(novo_participante):
    return novo_participante("ana@example.com", nome="Ana")


def pedir(cliente, email):
    return cliente.postar(URL, {"email": email})


def credenciais(usuario):
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    return uid, default_token_generator.make_token(usuario)


def redefinir(cliente, uid, token, senha=SENHA_NOVA):
    return cliente.postar(URL_REDEFINIR, {"uid": uid, "token": token, "nova_senha": senha})


def link_do_email() -> str:
    recuperacao.aguardar_envios()
    return re.search(r"https?://\S+", mail.outbox[-1].body).group(0)


# ---------- pedido ----------


def test_req_20_1_conta_existente_recebe_o_link_em_portugues(cliente, ana):
    """[011] REQ-20.1: 202, um e-mail para o endereço da conta, com o link de redefinição."""
    resposta = pedir(cliente, "ana@example.com")
    recuperacao.aguardar_envios()

    assert resposta.status_code == 202
    assert resposta.json() == {"detalhe": MENSAGEM}
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == ["ana@example.com"]
    assert email.subject == "Entrelinhas — redefinir senha"
    assert "Se não foi você, ignore" in email.body
    assert "1 hora" in email.body
    link = link_do_email()
    uid, token = re.search(r"#/redefinir/([^/\s]+)/([^/\s]+)", link).groups()
    assert uid == urlsafe_base64_encode(force_bytes(ana.pk))
    assert default_token_generator.check_token(ana, token)


@pytest.mark.parametrize("email", ["ANA@Example.COM", "  ana@example.com  "])
def test_req_20_1_maiusculas_e_espacos_acham_a_conta(cliente, ana, email):
    """[011] REQ-20.1 / PROP-14: o e-mail é normalizado."""
    assert pedir(cliente, email).status_code == 202
    recuperacao.aguardar_envios()

    assert len(mail.outbox) == 1


@pytest.mark.parametrize(
    "email",
    [
        "ninguem@example.com",
        "",
        "   ",
        "sem-arroba",
        "a@",
        "@b.com",
        "x" * 300 + "@a.com",
        5,
        None,
        ["ana@example.com"],
    ],
)
def test_req_20_2_sem_conta_ou_mal_formado_responde_igual_e_nao_envia(cliente, ana, email):
    """[011] REQ-20.2 / ABU-24."""
    resposta = pedir(cliente, email)
    recuperacao.aguardar_envios()

    assert resposta.status_code == 202
    assert resposta.json() == {"detalhe": MENSAGEM}
    assert mail.outbox == []
    assert PedidoRecuperacao.objects.count() == 0


def test_req_20_2_corpo_que_nao_e_objeto_tambem_responde_igual(cliente, ana):
    """[011] REQ-20.2 / ABU-24."""
    resposta = cliente.postar(URL, ["ana@example.com"])

    assert resposta.status_code == 202 and resposta.json() == {"detalhe": MENSAGEM}
    assert mail.outbox == []


def test_req_20_2_conta_inativa_nao_recebe(cliente, novo_participante):
    """[011] REQ-20.2: conta desativada se comporta como sem conta."""
    novo_participante("inativa@example.com", nome="Inativa", ativo=False)

    resposta = pedir(cliente, "inativa@example.com")
    recuperacao.aguardar_envios()

    assert resposta.status_code == 202 and mail.outbox == []


def test_abu_24_prop_14_a_resposta_e_identica_com_e_sem_conta(cliente, ana):
    """[011] PROP-14 / ABU-24: status, corpo e cabeçalhos relevantes não diferenciam as entradas."""
    casos = [
        "ana@example.com",
        "ANA@example.com",
        "ninguem@example.com",
        "",
        "lixo",
        "x" * 400,
        "ana@example.com",
    ]
    respostas = [pedir(cliente, e) for e in casos]
    recuperacao.aguardar_envios()

    def impressao(r):
        cab = {
            k.lower(): v
            for k, v in r.headers.items()
            if k.lower() not in ("date", "set-cookie", "vary")
        }
        return r.status_code, r.content, cab

    assert len({repr(impressao(r)) for r in respostas}) == 1
    assert len(mail.outbox) == 3, (
        "só as três entradas que são da conta enviam (o limite é de 3 por hora)"
    )


def test_req_20_3_abu_27_o_link_usa_a_base_de_configuracao_e_nao_o_host_do_pedido(cliente, ana):
    """[011] REQ-20.3 / ABU-27: X-Forwarded-Host e campos extras do atacante não entram no link."""
    resposta = cliente.post(
        URL,
        {
            "email": "ana@example.com",
            "base": "https://evil.example.org",
            "url": "https://evil.example.org",
        },
        format="json",
        HTTP_X_CSRFTOKEN=cliente.token(),
        HTTP_X_FORWARDED_HOST="evil.example.org",
    )
    recuperacao.aguardar_envios()

    assert resposta.status_code == 202
    link = link_do_email()
    assert link.startswith(BASE + "#/redefinir/")
    assert "evil" not in mail.outbox[0].body


def test_abu_27_um_host_falso_e_recusado_antes_de_qualquer_envio(cliente, ana):
    """[011] ABU-27: `Host` fora de `ALLOWED_HOSTS` nem chega ao pedido."""
    resposta = cliente.post(
        URL,
        {"email": "ana@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=cliente.token(),
        HTTP_HOST="evil.example.org",
    )
    recuperacao.aguardar_envios()

    assert resposta.status_code == 400
    assert mail.outbox == []


def test_req_20_3_o_link_vai_no_fragmento(cliente, ana):
    """[011] REQ-20.3: o token nunca vai ao servidor nem a logs de acesso."""
    pedir(cliente, "ana@example.com")

    link = link_do_email()

    assert "#/redefinir/" in link
    assert "?" not in link.split("#")[0]


class SmtpLento(BaseEmailBackend):
    def send_messages(self, mensagens):
        time.sleep(2)
        mail.outbox.extend(mensagens)
        return len(mensagens)


def test_req_20_4_o_envio_nao_atrasa_a_resposta(cliente, ana, settings):
    """[011] REQ-20.4: SMTP de 2 s; a resposta volta em bem menos, e o e-mail chega depois."""
    settings.EMAIL_BACKEND = "apps.acesso.tests.test_recuperacao.SmtpLento"

    inicio = time.monotonic()
    resposta = pedir(cliente, "ana@example.com")
    demorou = time.monotonic() - inicio

    assert resposta.status_code == 202
    assert demorou < 1.0, demorou
    assert mail.outbox == [], "o e-mail ainda está a caminho"
    recuperacao.aguardar_envios()
    assert len(mail.outbox) == 1


class SmtpQuebrado(BaseEmailBackend):
    def send_messages(self, mensagens):
        raise ConnectionRefusedError(f"falhou para {mensagens[0].to[0]} com {mensagens[0].body}")


def test_req_20_5_falha_de_envio_nao_muda_a_resposta_e_o_log_nao_vaza(
    cliente, ana, settings, caplog
):
    """[011] REQ-20.5 / CTL-93: nem e-mail, nem token, nem corpo, nem senha do SMTP no log."""
    settings.EMAIL_BACKEND = "apps.acesso.tests.test_recuperacao.SmtpQuebrado"

    with caplog.at_level(logging.DEBUG):
        resposta = pedir(cliente, "ana@example.com")
        recuperacao.aguardar_envios()

    assert resposta.status_code == 202 and resposta.json() == {"detalhe": MENSAGEM}
    registrado = "\n".join(r.getMessage() for r in caplog.records)
    assert "ana@example.com" not in registrado
    assert "redefinir" not in registrado
    assert "SENHA-SMTP" not in registrado
    assert "falhou" in registrado, "a falha precisa deixar rastro (sem dado sensível)"


def test_req_20_6_abu_25_no_maximo_3_emails_por_conta_por_hora(cliente, ana, monkeypatch):
    """[011] REQ-20.6 / ABU-25: o 4º pedido responde igual e não envia; uma hora depois volta a enviar."""
    agora = [datetime(2026, 11, 5, 12, 0, tzinfo=__import__("datetime").timezone.utc)]
    monkeypatch.setattr(recuperacao, "agora", lambda: agora[0])

    respostas = [pedir(cliente, "ana@example.com") for _ in range(5)]
    recuperacao.aguardar_envios()

    assert {r.status_code for r in respostas} == {202}
    assert len({r.content for r in respostas}) == 1
    assert len(mail.outbox) == 3
    assert PedidoRecuperacao.objects.count() == 3

    agora[0] += timedelta(minutes=61)
    pedir(cliente, "ana@example.com")
    recuperacao.aguardar_envios()
    assert len(mail.outbox) == 4


def test_req_20_6_o_limite_e_por_conta_e_nao_global(cliente, ana, novo_participante):
    """[011] REQ-20.6: outra conta tem os próprios 3."""
    novo_participante("bia@example.com", nome="Bia")
    for _ in range(4):
        pedir(cliente, "ana@example.com")
    pedir(cliente, "bia@example.com")
    recuperacao.aguardar_envios()

    destinos = sorted(m.to[0] for m in mail.outbox)
    assert destinos == ["ana@example.com"] * 3 + ["bia@example.com"]


def test_req_20_6_pedidos_com_mais_de_24h_sao_apagados(cliente, ana, monkeypatch):
    """[011] LGPD: retenção de 24 horas do registro de pedidos."""
    agora = [datetime(2026, 11, 5, 12, 0, tzinfo=__import__("datetime").timezone.utc)]
    monkeypatch.setattr(recuperacao, "agora", lambda: agora[0])
    pedir(cliente, "ana@example.com")
    agora[0] += timedelta(hours=25)

    pedir(cliente, "ana@example.com")

    assert PedidoRecuperacao.objects.count() == 1


# ---------- redefinição ----------


def test_req_21_1_token_valido_troca_a_senha_encerra_sessoes_e_nao_abre_sessao(cliente, ana, logar):
    """[011] REQ-21.1: 204, senha nova vale, a antiga não, sessão antiga morre, nada de login automático."""
    antigo = logar("ana@example.com")
    assert antigo.get("/api/v1/perfil").status_code == 200
    ana.refresh_from_db()  # o login mudou o `last_login`, que entra no token
    uid, token = credenciais(ana)

    resposta = redefinir(cliente, uid, token)

    assert resposta.status_code == 204
    assert "sessionid" not in "".join(resposta.cookies.keys())
    assert antigo.get("/api/v1/perfil").status_code in (401, 403), "a sessão antiga foi encerrada"
    from django.contrib.sessions.models import Session

    assert not any(
        s.get_decoded().get("_auth_user_id") == str(ana.pk) for s in Session.objects.all()
    ), "as sessões da conta saíram do banco"
    assert cliente.get("/api/v1/perfil").status_code in (401, 403), "e a pessoa não entrou sozinha"
    novo = Cliente()
    assert novo.entrar("ana@example.com", SENHA).status_code == 400
    assert novo.entrar("ana@example.com", SENHA_NOVA).status_code == 200


def test_req_21_4_depois_de_redefinir_vai_um_email_de_aviso(cliente, ana):
    """[011] REQ-21.4."""
    uid, token = credenciais(ana)

    redefinir(cliente, uid, token)
    recuperacao.aguardar_envios()

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["ana@example.com"]
    assert "senha foi alterada" in mail.outbox[0].subject.lower()
    assert SENHA_NOVA not in mail.outbox[0].body


def test_req_21_2_abu_26_uid_ou_token_invalidos_da_400_sempre_igual(
    cliente, ana, novo_participante
):
    """[011] REQ-21.2 / ABU-26: malformado, trocado, de outra pessoa, nulo: a mesma resposta e nada muda."""
    bia = novo_participante("bia@example.com", nome="Bia")
    uid, token = credenciais(ana)
    uid_bia, token_bia = credenciais(bia)
    casos = [
        ("", ""),
        (uid, "token-que-nao-existe"),
        (uid, token[:-1] + ("a" if token[-1] != "a" else "b")),
        (uid_bia, token),  # uid trocado
        (uid, token_bia),
        ("###", token),
        (urlsafe_base64_encode(b"999999"), token),
        (urlsafe_base64_encode(b"texto"), token),
        (None, None),
    ]
    respostas = [
        cliente.postar(URL_REDEFINIR, {"uid": u, "token": t, "nova_senha": SENHA_NOVA})
        for u, t in casos
    ]

    assert {r.status_code for r in respostas} == {400}
    assert len({r.content for r in respostas}) == 1
    assert respostas[0].json() == {"detalhe": "Link inválido ou vencido."}
    ana.refresh_from_db()
    assert ana.check_password(SENHA), "nada foi alterado"


@pytest.mark.parametrize(
    "corpo", [{}, {"uid": "x"}, [], "texto", {"uid": 5, "token": 5, "nova_senha": 5}]
)
def test_req_21_2_corpo_mal_formado_da_400_ou_422_nunca_500(cliente, corpo):
    """[011] REQ-21.2 / NFR-REC-2."""
    resposta = cliente.postar(URL_REDEFINIR, corpo)

    assert resposta.status_code in (400, 422)


def test_req_21_2_token_vencido_depois_de_1_hora(cliente, ana, monkeypatch):
    """[011] REQ-21.2: 59 min ainda vale; 61 min não (relógio injetado no gerador de tokens do Django)."""
    uid, token = credenciais(ana)
    agora = datetime.now()

    monkeypatch.setattr(
        type(default_token_generator), "_now", lambda self: agora + timedelta(minutes=59)
    )
    assert redefinir(cliente, uid, token, "curta").status_code == 422, (
        "dentro do prazo: chega à política"
    )
    monkeypatch.setattr(
        type(default_token_generator), "_now", lambda self: agora + timedelta(minutes=61)
    )
    resposta = redefinir(cliente, uid, token)

    assert resposta.status_code == 400
    ana.refresh_from_db()
    assert ana.check_password(SENHA)


def test_req_21_2_21_5_o_token_nao_vale_duas_vezes(cliente, ana):
    """[011] REQ-21.5."""
    uid, token = credenciais(ana)

    assert redefinir(cliente, uid, token).status_code == 204
    segunda = redefinir(cliente, uid, token, "outra-senha-comprida-e-boa-77")

    assert segunda.status_code == 400
    ana.refresh_from_db()
    assert ana.check_password(SENHA_NOVA)


def test_req_21_3_senha_fraca_da_422_sem_alterar_e_o_token_continua_valendo(cliente, ana):
    """[011] REQ-21.3: curta, comum e numérica; depois uma boa funciona com o mesmo token."""
    uid, token = credenciais(ana)

    for fraca in ("curta", "password1234", "12345678901234567890", "ana@example.com"):
        resposta = redefinir(cliente, uid, token, fraca)
        assert resposta.status_code == 422, fraca
        assert "nova_senha" in resposta.json()["campos"]
    ana.refresh_from_db()
    assert ana.check_password(SENHA)

    assert redefinir(cliente, uid, token).status_code == 204


def test_req_21_5_trocar_a_senha_por_outro_caminho_mata_o_token(cliente, ana):
    """[011] REQ-21.5: troca pelo perfil (003) ou redefinição pelo Admin."""
    uid, token = credenciais(ana)
    ana.set_password("senha-trocada-pelo-admin-55")
    ana.save()

    assert redefinir(cliente, uid, token).status_code == 400


def test_req_21_5_entrar_de_novo_tambem_mata_o_token(cliente, ana, logar):
    """[011] REQ-21.5: o `last_login` entra no token do Django."""
    uid, token = credenciais(ana)
    logar("ana@example.com")

    assert redefinir(cliente, uid, token).status_code == 400


def test_req_21_2_conta_desativada_nao_redefine(cliente, ana):
    """[011] REQ-21.2."""
    uid, token = credenciais(ana)
    ana.is_active = False
    ana.save()

    assert redefinir(cliente, uid, token).status_code == 400


def test_nfr_rec_1_a_senha_do_smtp_nao_aparece_em_nenhuma_resposta(cliente, ana):
    """[011] NFR-REC-1: respostas do pedido e da redefinição não a trazem."""
    respostas = [pedir(cliente, "ana@example.com"), redefinir(cliente, "x", "y")]

    for r in respostas:
        assert "SENHA-SMTP" not in r.content.decode()


def test_ctl_91_as_duas_rotas_exigem_csrf(db, ana):
    """[011] CTL-91: sem o token de CSRF o POST é recusado, como nas outras rotas públicas."""
    sem_token = Cliente()

    assert sem_token.post(URL, {"email": "ana@example.com"}, format="json").status_code == 403
    assert (
        sem_token.post(
            URL_REDEFINIR, {"uid": "a", "token": "b", "nova_senha": "c"}, format="json"
        ).status_code
        == 403
    )


def test_limpar_pedidos_apaga_os_antigos(ana):
    """[011] LGPD / T-3.2: o comando de limpeza do deploy."""
    from django.core.management import call_command
    from django.utils import timezone

    PedidoRecuperacao.objects.create(usuario=ana)
    antigo = PedidoRecuperacao.objects.create(usuario=ana)
    PedidoRecuperacao.objects.filter(pk=antigo.pk).update(
        criado_em=timezone.now() - timedelta(hours=30)
    )

    call_command("limpar_pedidos")

    assert PedidoRecuperacao.objects.count() == 1


def test_usuario_model_continua_com_email_unico_para_a_recuperacao(ana):
    """[011]: sanidade: o e-mail da conta é o `email` do usuário (a recuperação não cria outro campo)."""
    assert get_user_model().objects.get(email="ana@example.com").pk == ana.pk
