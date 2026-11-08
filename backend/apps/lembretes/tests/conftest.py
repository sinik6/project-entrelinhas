# ruff: noqa: F811
"""Suporte dos testes da 010: assinaturas válidas, usuários e entregas criados direto no banco, relógio e envio falsos."""

import base64
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from apps.acesso.models import Grupo, Perfil
from apps.fotos.tests.conftest import dono, parceiro  # noqa: F401
from apps.registros.models import Registro
from apps.registros.tests.conftest import (  # noqa: F401
    AMBAR,
    SENHA,
    VERDE,
    Cliente,
    cliente,
    estranho,
    grupo_do_dono,
    logar,
    novo_grupo,
    novo_participante,
    pasta_de_fotos,
    relogio,
)

SP = ZoneInfo("America/Sao_Paulo")
FCM = "https://fcm.googleapis.com/fcm/send/abc123"


def b64url(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


def chaves_validas() -> dict:
    """p256dh de 65 bytes (ponto não comprimido) e auth de 16 bytes, como um navegador manda."""
    return {"p256dh": b64url(b"\x04" + bytes(range(64))), "auth": b64url(bytes(range(16)))}


def assinatura(endpoint=FCM, **chaves) -> dict:
    return {"endpoint": endpoint, "keys": {**chaves_validas(), **chaves}}


def assinar(cliente, endpoint=FCM, **chaves):
    return cliente.postar("/api/v1/lembretes/assinaturas", assinatura(endpoint, **chaves))


def desassinar(cliente, endpoint=FCM):
    return cliente.delete(
        "/api/v1/lembretes/assinaturas",
        {"endpoint": endpoint},
        format="json",
        HTTP_X_CSRFTOKEN=cliente.token(),
    )


def sp(ano, mes, dia, hora, minuto=0, segundo=0) -> datetime:
    """Um instante dado no relógio de São Paulo, já como `datetime` com fuso (o que o disparador recebe)."""
    return datetime(ano, mes, dia, hora, minuto, segundo, tzinfo=SP)


@pytest.fixture
def pessoas(db):
    """Fábrica de pessoas no mesmo grupo, com assinaturas: `criar('ana', n_assinaturas=1)` -> usuário."""
    grupo = Grupo.objects.create()
    contador = {"n": 0}

    def criar(nome, n_assinaturas=1, com_grupo=True):
        usuario = get_user_model().objects.create_user(
            username=f"{nome}@example.com", email=f"{nome}@example.com", password=SENHA
        )
        contador["n"] += 1
        Perfil.objects.create(
            usuario=usuario,
            nome=nome.capitalize(),
            cor=f"#{contador['n']:06X}".replace("#0000", "#4D7C"),
            grupo=grupo if com_grupo else None,
        )
        from apps.lembretes.models import AssinaturaPush

        for i in range(n_assinaturas):
            AssinaturaPush.objects.create(
                usuario=usuario,
                endpoint=f"https://fcm.googleapis.com/fcm/send/{nome}-{i}",
                p256dh="p",
                auth="a",
            )
        return usuario

    criar.grupo = grupo
    return criar


def entregou(usuario, dia: date, grupo=None):
    return Registro.objects.create(
        grupo=grupo or usuario.perfil.grupo,
        autor=usuario,
        data=dia,
        texto="registro de teste, com texto suficiente",
        visibilidade="full",
        entregue_em=datetime(dia.year, dia.month, dia.day, 12, tzinfo=UTC) + timedelta(hours=3),
    )


class EnvioFalso:
    """Substitui o envio real: guarda o que foi enviado e responde `ok`, `gone` ou `falha` conforme o teste mandar."""

    def __init__(self):
        self.chamadas = []
        self.respostas = {}

    def __call__(self, assinatura, carga):
        self.chamadas.append((assinatura.usuario_id, assinatura.endpoint, carga))
        resposta = self.respostas.get(assinatura.endpoint, "ok")
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    @property
    def usuarios(self):
        return sorted({u for u, _, _ in self.chamadas})


@pytest.fixture
def envio():
    return EnvioFalso()
