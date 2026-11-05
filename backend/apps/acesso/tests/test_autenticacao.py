"""[003] Autenticação por e-mail e senha, sessão, CSRF e cookies (US-1, ABU-2, ABU-4, NFR-SEC-1)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from apps.acesso.tests.conftest import SENHA, Cliente

BACKEND = Path(__file__).resolve().parents[3]
FALHA = {"detalhe": "E-mail ou senha incorretos."}


def test_req_1_4_endpoint_csrf_e_publico_e_devolve_token_e_cookie(cliente):
    """[003] REQ-1.4: o token de proteção é público e vem junto do cookie com o segredo."""
    resposta = cliente.get("/api/v1/auth/csrf")

    assert resposta.status_code == 200
    assert len(resposta.json()["token"]) >= 32
    assert "entrelinhas_csrftoken" in resposta.cookies


def test_req_1_1_entrar_cria_sessao(cliente, novo_participante):
    """[003] REQ-1.1: e-mail e senha corretos iniciam a sessão e devolvem o perfil."""
    novo_participante("ana@example.com", nome="Ana")

    resposta = cliente.entrar("ana@example.com")

    assert resposta.status_code == 200
    assert resposta.json()["email"] == "ana@example.com"
    assert resposta.json()["nome"] == "Ana"
    assert cliente.get("/api/v1/perfil").status_code == 200


def test_req_1_1_email_com_caixa_diferente_tambem_entra(cliente, novo_participante):
    """[003] REQ-1.1: o e-mail não diferencia maiúsculas de minúsculas."""
    novo_participante("ana@example.com")

    assert cliente.entrar("  ANA@Example.com ").status_code == 200


def test_req_1_1_a_conta_do_administrador_entra_pelo_email_dela(cliente, novo_participante):
    """[003] REQ-1.1: a conta do administrador (username diferente do e-mail, sem perfil) entra pelo e-mail."""
    from django.contrib.auth import get_user_model

    get_user_model().objects.create_superuser("jpjamal", "dono@example.com", SENHA)

    resposta = cliente.entrar("dono@example.com")

    assert resposta.status_code == 200
    assert resposta.json()["completo"] is False


def test_ctl_16_entrar_troca_a_chave_de_uma_sessao_anonima_existente(cliente, novo_participante):
    """[003] CTL-16: uma sessão plantada antes do login não passa a valer logada (sem fixação de sessão)."""
    novo_participante("ana@example.com")
    sessao = cliente.session  # cria uma sessão anônima e põe o cookie dela no cliente
    sessao["plantada"] = True
    sessao.save()
    plantada = sessao.session_key

    assert cliente.entrar("ana@example.com").status_code == 200

    assert cliente.cookies["entrelinhas_sessionid"].value != plantada
    atacante = Cliente()
    atacante.cookies["entrelinhas_sessionid"] = plantada
    assert atacante.get("/api/v1/perfil").status_code == 401


def test_req_1_2_entrar_falha_igual_para_senha_errada_e_email_inexistente(
    cliente, novo_participante
):
    """[003] REQ-1.2 / PROP-4: mesma resposta (status e corpo) com e-mail existente e inexistente."""
    novo_participante("ana@example.com")

    senha_errada = cliente.entrar("ana@example.com", "senha-errada-123456")
    sem_conta = cliente.entrar("ninguem@example.com", SENHA)

    assert senha_errada.status_code == sem_conta.status_code == 400
    assert senha_errada.json() == sem_conta.json() == FALHA


def test_req_1_2_conta_inativa_responde_igual(cliente, novo_participante):
    """[003] REQ-1.2: conta inativa não se distingue de senha errada."""
    novo_participante("ana@example.com", ativo=False)

    assert cliente.entrar("ana@example.com").json() == FALHA


def test_abu_2_entrar_nao_revela_se_o_email_existe(cliente, novo_participante):
    """[003] ABU-2: nem corpo, nem status, nem cookie de sessão diferem entre e-mail com e sem conta."""
    novo_participante("ana@example.com")

    com_conta = cliente.entrar("ana@example.com", "senha-errada-123456")
    sem_conta = cliente.entrar("ninguem@example.com", "senha-errada-123456")

    assert (com_conta.status_code, com_conta.json()) == (sem_conta.status_code, sem_conta.json())
    assert "entrelinhas_sessionid" not in com_conta.cookies
    assert "entrelinhas_sessionid" not in sem_conta.cookies


def test_req_1_3_sair_encerra_a_sessao_no_servidor(novo_participante, logar):
    """[003] REQ-1.3: depois de sair, o cookie antigo não vale mais, mesmo se alguém o guardou."""
    novo_participante("ana@example.com")
    cliente = logar("ana@example.com")
    guardado = cliente.cookies["entrelinhas_sessionid"].value

    assert cliente.postar("/api/v1/auth/sair").status_code == 204

    outro = Cliente()
    outro.cookies["entrelinhas_sessionid"] = guardado
    assert outro.get("/api/v1/perfil").status_code == 401


def test_req_1_4_rotas_protegidas_respondem_401_sem_sessao(cliente):
    """[003] REQ-1.4: sem login, tudo o que não é token, entrar ou aceitar convite recusa."""
    assert cliente.get("/api/v1/perfil").status_code == 401
    assert cliente.get("/api/v1/grupo").status_code == 401
    assert cliente.alterar("/api/v1/perfil", {"nome": "X"}).status_code == 401
    for rota in (
        "/api/v1/auth/sair",
        "/api/v1/perfil/senha",
        "/api/v1/grupo",
        "/api/v1/grupo/convites",
    ):
        assert cliente.postar(rota).status_code == 401, rota


@pytest.mark.parametrize("rota", ["/api/v1/auth/entrar", "/api/v1/convites/aceitar"])
def test_abu_4_post_sem_token_de_protecao_e_recusado_ate_em_rota_anonima(cliente, rota):
    """[003] ABU-4 / CTL-15: entrar e aceitar convite exigem o token, apesar de anônimos."""
    sem_token = cliente.post(rota, {"email": "a@example.com", "senha": SENHA}, format="json")
    token_falso = cliente.post(rota, {}, format="json", HTTP_X_CSRFTOKEN="token-falso")

    assert sem_token.status_code == 403
    assert token_falso.status_code == 403


def test_abu_4_token_de_outro_navegador_nao_vale(cliente):
    """[003] ABU-4: o token vale só junto do cookie que o gerou."""
    outro = Cliente()
    token_de_outro = outro.token()
    cliente.get("/api/v1/auth/csrf")

    resposta = cliente.post(
        "/api/v1/auth/entrar", {}, format="json", HTTP_X_CSRFTOKEN=token_de_outro
    )

    assert resposta.status_code == 403


def test_nfr_sec_1_cookies_httponly_samesite_com_nome_proprio(cliente, novo_participante):
    """[003] NFR-SEC-1 / CTL-16: nomes próprios, HttpOnly e SameSite=Lax nos dois cookies."""
    novo_participante("ana@example.com")
    cliente.get("/api/v1/auth/csrf")
    cliente.entrar("ana@example.com")

    for nome in ("entrelinhas_csrftoken", "entrelinhas_sessionid"):
        cookie = cliente.cookies[nome]
        assert cookie["httponly"], nome
        assert cookie["samesite"] == "Lax", nome
    assert "sessionid" not in cliente.cookies
    assert "csrftoken" not in cliente.cookies


def test_nfr_sec_1_producao_cookies_seguros_e_no_caminho_do_prefixo():
    """[003] NFR-SEC-1 / CTL-16: em produção os cookies são Secure e só valem sob /entrelinhas/."""
    codigo = (
        "from django.conf import settings as s; "
        "print(s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, s.SESSION_COOKIE_PATH, s.CSRF_COOKIE_PATH, "
        "s.SESSION_COOKIE_NAME, s.CSRF_COOKIE_NAME, s.CSRF_COOKIE_HTTPONLY)"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "config.settings.prod",
            "DJANGO_SECRET_KEY": "x" * 60,
            "DJANGO_ALLOWED_HOSTS": "localhost",
            "DJANGO_PREFIXO_URL": "entrelinhas",
        },
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.split() == [
        "True",
        "True",
        "/entrelinhas/",
        "/entrelinhas/",
        "entrelinhas_sessionid",
        "entrelinhas_csrftoken",
        "True",
    ]
