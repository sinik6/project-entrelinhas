# ruff: noqa: F811
# (as fábricas das mudanças anteriores são importadas e depois pedidas pelo nome nos parâmetros)
"""Suporte dos testes da 005: relógio controlável, entrega por API, marcadores únicos para provar o que vaza."""

from datetime import UTC, datetime

import pytest

from apps.fotos.tests.conftest import (  # noqa: F401
    AMBAR,
    SENHA,
    VERDE,
    Cliente,
    arquivos_em,
    cliente,
    dono,
    enviar_foto,
    estranho,
    grupo_do_dono,
    imagem_bytes,
    logar,
    novo_grupo,
    novo_participante,
    parceiro,
    pasta_de_fotos,
)

TEXTO_BASE = "Hoje escrevi um texto de teste bem comprido."


class Relogio:
    """Substitui `agora()` do serviço: o teste decide que horas são."""

    def __init__(self):
        self.valor = None

    def fixar(self, ano, mes, dia, hora=12, minuto=0, segundo=0):
        self.valor = datetime(ano, mes, dia, hora, minuto, segundo, tzinfo=UTC)

    def __call__(self):
        from django.utils import timezone

        return self.valor or timezone.now()


@pytest.fixture
def relogio(monkeypatch):
    r = Relogio()
    monkeypatch.setattr("apps.registros.services.agora", r)
    return r


def foto_manuscrito(cliente) -> str:
    resposta = enviar_foto(cliente, imagem_bytes("JPEG", (40, 30)))
    assert resposta.status_code == 201, resposta.content
    return resposta.json()["id"]


def entregar(cliente, texto=TEXTO_BASE, visibilidade="full", trecho=None, fotos=None, n_fotos=1):
    """Entrega um registro pela API. Sem `fotos`, envia `n_fotos` fotos de manuscrito antes."""
    if fotos is None:
        fotos = [foto_manuscrito(cliente) for _ in range(n_fotos)]
    corpo = {"texto": texto, "visibilidade": visibilidade, "fotos": fotos}
    if trecho is not None:
        corpo["trecho"] = trecho
    return cliente.postar("/api/v1/registros", corpo)


def marcadores(n: int) -> list[str]:
    """Marcadores ASCII únicos e de tamanho fixo (5): somem ou aparecem inteiros num trecho alinhado a 5."""
    return [f"~{k:03d}~" for k in range(n)]
