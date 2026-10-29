import logging
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client

SENHA = "correta-cavalo-bateria-grampo-7"
USUARIO = "dono"
EMAIL = "dono@example.com"

pytestmark = pytest.mark.django_db


def rodar(monkeypatch, *, usuario=USUARIO, email=EMAIL, senha=SENHA):
    """Executa o comando como o deploy: valores só no ambiente daquela execução."""
    for nome, valor in (
        ("ADMIN_USUARIO", usuario),
        ("ADMIN_EMAIL", email),
        ("SENHA_ADMIN_INICIAL", senha),
    ):
        if valor is None:
            monkeypatch.delenv(nome, raising=False)
        else:
            monkeypatch.setenv(nome, valor)
    saida, erro = StringIO(), StringIO()
    call_command("administrador_inicial", stdout=saida, stderr=erro)
    return saida.getvalue(), erro.getvalue()


def usuarios():
    return get_user_model().objects.all()


def test_req_1_1_cria_superusuario_quando_nao_existe(monkeypatch):
    """REQ-1.1: sem usuário com o nome configurado, cria o superusuário."""
    rodar(monkeypatch)

    usuario = usuarios().get(username=USUARIO)
    assert usuario.is_superuser
    assert usuario.is_staff
    assert usuario.email == EMAIL
    assert usuario.check_password(SENHA)


def test_req_1_2_usuario_existente_nao_muda(monkeypatch):
    """REQ-1.2: superusuário existente mantém senha, e-mail e permissões."""
    get_user_model().objects.create_superuser(
        USUARIO, "antigo@example.com", "outra-senha-longa-123"
    )

    saida, _ = rodar(monkeypatch, email="novo@example.com", senha=SENHA)

    usuario = usuarios().get(username=USUARIO)
    assert usuario.check_password("outra-senha-longa-123")
    assert not usuario.check_password(SENHA)
    assert usuario.email == "antigo@example.com"
    assert usuario.is_superuser
    assert "já existe" in saida


def test_req_1_3_conta_criada_entra_no_admin(monkeypatch):
    """REQ-1.3: a conta criada faz login no Admin com a senha configurada."""
    rodar(monkeypatch)
    cliente = Client()

    resposta = cliente.post(
        "/admin/login/", {"username": USUARIO, "password": SENHA, "next": "/admin/"}
    )

    assert resposta.status_code == 302
    assert resposta["Location"] == "/admin/"
    assert cliente.get("/admin/").status_code == 200


@pytest.mark.parametrize("senha", [None, ""])
def test_req_2_1_sem_senha_recusa_e_nao_cria(monkeypatch, senha):
    """REQ-2.1: senha não definida recusa e não cria usuário."""
    with pytest.raises(CommandError, match="SENHA_ADMIN_INICIAL"):
        rodar(monkeypatch, senha=senha)

    assert not usuarios().exists()


@pytest.mark.parametrize(
    "senha",
    [
        "Curta1!",  # abaixo do mínimo de 12
        "123456789012",  # só números
        "administrador123",  # parecida com o nome de usuário
    ],
)
def test_req_2_2_senha_fraca_recusa_e_nao_cria(monkeypatch, senha):
    """REQ-2.2 / PROP-2: senha recusada pela política nunca cria usuário."""
    with pytest.raises(CommandError, match="política de senhas"):
        rodar(monkeypatch, usuario="administrador", senha=senha)

    assert not usuarios().exists()


@pytest.mark.parametrize(
    ("usuario", "email"),
    [(None, EMAIL), ("", EMAIL), (USUARIO, None), (USUARIO, "")],
)
def test_req_2_3_sem_usuario_ou_email_recusa(monkeypatch, usuario, email):
    """REQ-2.3: nome de usuário ou e-mail não definidos recusam e não criam."""
    with pytest.raises(CommandError, match="ADMIN_USUARIO"):
        rodar(monkeypatch, usuario=usuario, email=email)

    assert not usuarios().exists()


def test_nfr_sec_1_senha_nao_aparece_na_saida(monkeypatch):
    """NFR-SEC-1: a saída do comando traz só o nome do usuário."""
    saida, erro = rodar(monkeypatch)

    assert saida.strip() == f"Administrador criado: {USUARIO}"
    assert erro == ""


def test_nfr_sec_2_senha_gravada_so_como_hash(monkeypatch):
    """NFR-SEC-2 / CTL-5: o banco guarda o hash, nunca a senha."""
    rodar(monkeypatch)

    gravado = usuarios().get(username=USUARIO).password
    assert SENHA not in gravado
    assert "$" in gravado


def test_abu_1_senha_nao_vai_para_saida_nem_para_log(monkeypatch, caplog):
    """ABU-1 / CTL-3: nem no sucesso nem no erro a senha é escrita."""
    caplog.set_level(logging.DEBUG)

    saida, erro = rodar(monkeypatch)
    with pytest.raises(CommandError, match="política de senhas") as falha:
        rodar(monkeypatch, usuario="administrador", senha="administrador123")

    assert SENHA not in saida + erro + caplog.text
    assert "administrador123" not in str(falha.value) + caplog.text


def test_abu_2_usuario_comum_existente_nao_e_promovido(monkeypatch):
    """ABU-2 / CTL-1: usuário comum com o mesmo nome não vira superusuário."""
    comum = get_user_model().objects.create_user(
        USUARIO, "comum@example.com", "senha-comum-longa-1"
    )

    with pytest.raises(CommandError, match="não é superusuário"):
        rodar(monkeypatch)

    comum.refresh_from_db()
    assert not comum.is_superuser
    assert not comum.is_staff
    assert comum.check_password("senha-comum-longa-1")


@pytest.mark.parametrize("senha", ["", "   ", " " * 12])
def test_abu_3_senha_vazia_ou_so_espacos_recusa(monkeypatch, senha):
    """ABU-3: senha vazia ou só de espaços é recusada, mesmo com 12 caracteres."""
    with pytest.raises(CommandError, match="SENHA_ADMIN_INICIAL"):
        rodar(monkeypatch, senha=senha)

    assert not usuarios().exists()


@pytest.mark.parametrize("execucoes", [2, 5])
def test_prop_1_repetir_a_execucao_nao_duplica_nem_troca_senha(monkeypatch, execucoes):
    """PROP-1: N execuções com os mesmos valores deixam um só usuário, com a senha da primeira."""
    for _ in range(execucoes):
        rodar(monkeypatch)

    assert usuarios().filter(username=USUARIO).count() == 1
    assert usuarios().get(username=USUARIO).check_password(SENHA)
