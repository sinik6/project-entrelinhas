"""Suporte comum dos testes da 003: cliente com CSRF de verdade e fábricas de participante e grupo."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.acesso.models import Grupo, Perfil

SENHA = "correta-cavalo-bateria-grampo-7"
OUTRA_SENHA = "outra-senha-longa-demais-9"
# Cores que passam na regra de contraste nos dois temas e são bem diferentes entre si.
VERDE, AMBAR, ROXO, CIANO = "#4D7C0F", "#B45309", "#9333EA", "#0E7490"


class Cliente(APIClient):
    """Cliente que exige CSRF como o navegador: busca o token em /auth/csrf e o manda no cabeçalho."""

    def __init__(self):
        super().__init__(enforce_csrf_checks=True)
        self._token = None

    def token(self):
        if self._token is None:
            resposta = self.get("/api/v1/auth/csrf")
            assert resposta.status_code == 200, resposta.content
            self._token = resposta.json()["token"]
        return self._token

    def esquecer_token(self):
        """Depois de entrar o Django renova o segredo do CSRF: o app precisa buscar o token de novo."""
        self._token = None

    def postar(self, url, dados=None):
        return self.post(
            url, dados if dados is not None else {}, format="json", HTTP_X_CSRFTOKEN=self.token()
        )

    def alterar(self, url, dados):
        return self.patch(url, dados, format="json", HTTP_X_CSRFTOKEN=self.token())

    def entrar(self, email, senha=SENHA):
        resposta = self.postar("/api/v1/auth/entrar", {"email": email, "senha": senha})
        self.esquecer_token()
        return resposta


@pytest.fixture
def cliente(db):
    return Cliente()


@pytest.fixture
def novo_grupo(db):
    def criar(limite_membros=2):
        return Grupo.objects.create(tipo="escrita", limite_membros=limite_membros)

    return criar


@pytest.fixture
def novo_participante(db):
    """Cria usuário (username = e-mail) e, se `nome` vier, o perfil. Sem `nome` imita a conta do administrador."""

    def criar(email, nome="Ana", cor=VERDE, grupo=None, senha=SENHA, ativo=True):
        usuario = get_user_model().objects.create_user(
            username=email, email=email, password=senha, is_active=ativo
        )
        if nome is not None:
            Perfil.objects.create(usuario=usuario, nome=nome, cor=cor, grupo=grupo)
        return usuario

    return criar


@pytest.fixture
def logar(db):
    def entrar(email, senha=SENHA):
        cliente = Cliente()
        resposta = cliente.entrar(email, senha)
        assert resposta.status_code == 200, resposta.content
        return cliente

    return entrar


@pytest.fixture
def grupo_do_dono(novo_participante, logar):
    """O dono com perfil completo, logado, com o grupo já criado pela API."""
    novo_participante("dono@example.com", nome="Dono", cor=VERDE)
    cliente = logar("dono@example.com")
    resposta = cliente.postar("/api/v1/grupo")
    assert resposta.status_code == 201, resposta.content
    return cliente
