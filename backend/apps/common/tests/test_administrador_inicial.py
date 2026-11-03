"""Testes da mudança 002 (administrador inicial). Os IDs REQ/NFR/ABU/PROP/CTL daqui são os da 002."""

import logging
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client

from apps.common import services

SENHA = "correta-cavalo-bateria-grampo-7"
USUARIO = "dono"
EMAIL = "dono@example.com"

pytestmark = pytest.mark.django_db


def rodar(monkeypatch, *, usuario=USUARIO, email=EMAIL, senha=SENHA, verificar=False):
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
    call_command("administrador_inicial", verificar=verificar, stdout=saida, stderr=erro)
    return saida.getvalue(), erro.getvalue()


def usuarios():
    return get_user_model().objects.all()


def test_req_1_1_cria_superusuario_quando_nao_existe(monkeypatch):
    """[002] REQ-1.1: sem usuário com o nome configurado, cria o superusuário."""
    rodar(monkeypatch)

    usuario = usuarios().get(username=USUARIO)
    assert usuario.is_superuser
    assert usuario.is_staff
    assert usuario.email == EMAIL
    assert usuario.check_password(SENHA)


def test_req_1_2_usuario_existente_nao_muda(monkeypatch):
    """[002] REQ-1.2: superusuário existente mantém senha, e-mail e permissões."""
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
    """[002] REQ-1.3: a conta criada faz login no Admin com a senha configurada."""
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
    """[002] REQ-2.1 / CTL-2: senha não definida recusa e não cria usuário."""
    with pytest.raises(CommandError, match="SENHA_ADMIN_INICIAL"):
        rodar(monkeypatch, senha=senha)

    assert not usuarios().exists()


@pytest.mark.parametrize(
    ("senha", "motivo"),
    [
        ("Curta1!", "pelo menos 12"),
        ("abcdefgh9!x", "pelo menos 12"),  # 11 caracteres: só o tamanho recusa
        ("123456789012", "numérica"),  # só números, 12 caracteres
        ("password1234", "muito comum"),  # 12 caracteres, só a lista de senhas comuns recusa
    ],
)
def test_req_2_2_senha_fraca_recusa_e_nao_cria(monkeypatch, senha, motivo):
    """[002] REQ-2.2 / PROP-2 / CTL-2: senha recusada pela política nunca cria usuário, e o motivo certo aparece."""
    with pytest.raises(CommandError, match=motivo):
        rodar(monkeypatch, senha=senha)

    assert not usuarios().exists()


def test_req_2_2_senha_parecida_com_o_usuario_recusa(monkeypatch):
    """[002] REQ-2.2 / CTL-2: senha parecida com o nome de usuário é recusada."""
    with pytest.raises(CommandError, match="muito parecida"):
        rodar(monkeypatch, usuario="administrador", senha="administrador123")

    assert not usuarios().exists()


def test_req_2_2_senha_de_12_caracteres_forte_e_aceita(monkeypatch):
    """[002] REQ-2.2: o mínimo é 12 (e não mais que isso): 12 caracteres fortes são aceitos."""
    rodar(monkeypatch, senha="abcdefgh9!xy")

    assert usuarios().filter(username=USUARIO).exists()


@pytest.mark.parametrize(
    ("usuario", "email"),
    [(None, EMAIL), ("", EMAIL), (USUARIO, None), (USUARIO, "")],
)
def test_req_2_3_sem_usuario_ou_email_recusa(monkeypatch, usuario, email):
    """[002] REQ-2.3: nome de usuário ou e-mail não definidos recusam e não criam."""
    with pytest.raises(CommandError, match="ADMIN_USUARIO"):
        rodar(monkeypatch, usuario=usuario, email=email)

    assert not usuarios().exists()


@pytest.mark.parametrize(
    ("usuario", "email", "variavel"),
    [
        (USUARIO, "sem-arroba", "ADMIN_EMAIL"),
        ("dono com espaço", EMAIL, "ADMIN_USUARIO"),
        ("a" * 151, EMAIL, "ADMIN_USUARIO"),
    ],
)
def test_req_2_3_usuario_ou_email_invalido_recusa_com_mensagem_limpa(
    monkeypatch, usuario, email, variavel
):
    """[002] REQ-2.3: nome ou e-mail inválidos recusam com CommandError, sem erro de banco."""
    with pytest.raises(CommandError, match=f"{variavel} inválido"):
        rodar(monkeypatch, usuario=usuario, email=email)

    assert not usuarios().exists()


def test_req_2_5_verificar_valida_sem_tocar_no_banco(monkeypatch, django_assert_num_queries):
    """[002] REQ-2.5: --verificar valida os valores e a política sem consultar nem gravar no banco."""
    with django_assert_num_queries(0):
        saida, _ = rodar(monkeypatch, verificar=True)

    assert "válida" in saida
    assert not usuarios().exists()


@pytest.mark.parametrize("senha", [None, "", "Curta1!", "password1234"])
def test_req_2_5_verificar_recusa_configuracao_ruim(monkeypatch, senha):
    """[002] REQ-2.5: --verificar recusa senha ausente, curta ou comum, para o deploy parar antes de derrubar a API."""
    with pytest.raises(CommandError):
        rodar(monkeypatch, senha=senha, verificar=True)

    assert not usuarios().exists()


def test_nfr_sec_1_senha_nao_aparece_na_saida(monkeypatch):
    """[002] NFR-SEC-1: a saída do comando traz só o nome do usuário."""
    saida, erro = rodar(monkeypatch)

    assert saida.strip() == f"Administrador criado: {USUARIO}"
    assert erro == ""


def test_nfr_sec_2_senha_gravada_so_como_hash(monkeypatch):
    """[002] NFR-SEC-2 / CTL-5: o banco guarda o hash, nunca a senha."""
    rodar(monkeypatch)

    gravado = usuarios().get(username=USUARIO).password
    assert SENHA not in gravado
    assert "$" in gravado


def test_abu_1_senha_nao_vai_para_saida_nem_para_log_no_sucesso(monkeypatch, caplog, capsys):
    """[002] ABU-1 / CTL-3: no sucesso a senha não aparece na saída do comando, do processo nem no log."""
    caplog.set_level(logging.DEBUG)

    saida, erro = rodar(monkeypatch)
    processo = capsys.readouterr()

    assert SENHA not in saida + erro + processo.out + processo.err + caplog.text


@pytest.mark.parametrize(
    "cenario",
    [
        {"email": "sem-arroba"},
        {"usuario": "dono com espaço"},
        {"senha": "Curta1!"},
        {"senha": "password1234"},
        {"usuario": "administrador", "senha": "administrador123"},
    ],
)
def test_abu_1_senha_nao_vai_para_nenhuma_saida_nos_erros(monkeypatch, caplog, capsys, cenario):
    """[002] ABU-1 / CTL-3: em cada erro de validação a senha não vai para a mensagem, a saída nem o log."""
    caplog.set_level(logging.DEBUG)
    senha = cenario.get("senha", SENHA)

    with pytest.raises(CommandError) as falha:
        rodar(monkeypatch, **cenario)
    processo = capsys.readouterr()

    assert senha not in str(falha.value) + processo.out + processo.err + caplog.text


def test_abu_1_senha_nao_vai_para_nenhuma_saida_quando_ha_usuario_comum(
    monkeypatch, caplog, capsys
):
    """[002] ABU-1 / CTL-3: a recusa por usuário comum existente também não escreve a senha."""
    get_user_model().objects.create_user(USUARIO, EMAIL, "senha-comum-longa-1")
    caplog.set_level(logging.DEBUG)

    with pytest.raises(CommandError) as falha:
        rodar(monkeypatch)
    processo = capsys.readouterr()

    assert SENHA not in str(falha.value) + processo.out + processo.err + caplog.text


def test_abu_1_verificar_nao_escreve_a_senha(monkeypatch, caplog, capsys):
    """[002] ABU-1 / CTL-3: `--verificar` também não escreve a senha."""
    caplog.set_level(logging.DEBUG)

    saida, erro = rodar(monkeypatch, verificar=True)
    processo = capsys.readouterr()

    assert SENHA not in saida + erro + processo.out + processo.err + caplog.text


def test_abu_2_usuario_comum_existente_nao_e_promovido(monkeypatch):
    """[002] ABU-2 / CTL-1: usuário comum com o mesmo nome não vira superusuário."""
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
    """[002] ABU-3 / CTL-2: senha vazia ou só de espaços é recusada, mesmo com 12 caracteres."""
    with pytest.raises(CommandError, match="SENHA_ADMIN_INICIAL"):
        rodar(monkeypatch, senha=senha)

    assert not usuarios().exists()


@pytest.mark.parametrize("execucoes", [2, 5])
def test_prop_1_repetir_a_execucao_nao_duplica_nem_troca_senha(monkeypatch, execucoes):
    """[002] PROP-1: N execuções com os mesmos valores deixam um só usuário, com a senha da primeira."""
    for _ in range(execucoes):
        rodar(monkeypatch)

    assert usuarios().filter(username=USUARIO).count() == 1
    assert usuarios().get(username=USUARIO).check_password(SENHA)


def test_prop_1_corrida_entre_duas_execucoes_superusuario_vira_ja_existe(monkeypatch):
    """[002] PROP-1: se outra execução criou o mesmo superusuário entre a busca e a criação, vale "já existe"."""
    get_user_model().objects.create_superuser(USUARIO, EMAIL, "outra-senha-longa-123")
    monkeypatch.setattr(services, "_buscar", lambda modelo, usuario: None)

    saida, _ = rodar(monkeypatch)

    assert "já existe" in saida
    assert usuarios().get(username=USUARIO).check_password("outra-senha-longa-123")
    assert usuarios().filter(username=USUARIO).count() == 1


def test_abu_2_corrida_entre_duas_execucoes_usuario_comum_nao_e_promovido(monkeypatch):
    """[002] ABU-2: na corrida, um usuário comum criado no intervalo também não é promovido."""
    comum = get_user_model().objects.create_user(USUARIO, EMAIL, "senha-comum-longa-1")
    monkeypatch.setattr(services, "_buscar", lambda modelo, usuario: None)

    with pytest.raises(CommandError, match="não é superusuário"):
        rodar(monkeypatch)

    comum.refresh_from_db()
    assert not comum.is_superuser


def test_req_1_2_nome_em_forma_unicode_nao_normalizada_acha_a_conta_existente(monkeypatch):
    """[002] REQ-1.2: o nome é normalizado (NFKC) como o Django faz, então a conta existente é achada."""
    get_user_model().objects.create_superuser(
        "admin", "antigo@example.com", "outra-senha-longa-123"
    )

    saida, _ = rodar(monkeypatch, usuario="ａdmin")

    assert "já existe: admin" in saida
    assert usuarios().count() == 1


def test_abu_2_nome_que_so_difere_na_caixa_recusa_usuario_comum(monkeypatch):
    """[002] ABU-2: `Dono` comum existente e `dono` configurado são o mesmo nome: recusa, não cria um segundo."""
    get_user_model().objects.create_user("Dono", EMAIL, "senha-comum-longa-1")

    with pytest.raises(CommandError, match="não é superusuário"):
        rodar(monkeypatch)

    assert usuarios().count() == 1


def test_req_1_2_nome_que_so_difere_na_caixa_acha_o_superusuario(monkeypatch):
    """[002] REQ-1.2: `Dono` superusuário existente e `dono` configurado: já existe, sem criar outro."""
    get_user_model().objects.create_superuser("Dono", EMAIL, "outra-senha-longa-123")

    saida, _ = rodar(monkeypatch)

    assert "já existe" in saida
    assert usuarios().count() == 1


def test_req_1_4_superusuario_inativo_avisa_sem_alterar(monkeypatch):
    """[002] REQ-1.4: superusuário existente e inativo continua "já existe", mas o aviso aparece e nada muda."""
    existente = get_user_model().objects.create_superuser(USUARIO, EMAIL, "outra-senha-longa-123")
    existente.is_active = False
    existente.save()

    saida, erro = rodar(monkeypatch)

    existente.refresh_from_db()
    assert "já existe" in saida
    assert "inativo" in erro
    assert existente.is_active is False
    assert existente.check_password("outra-senha-longa-123")
