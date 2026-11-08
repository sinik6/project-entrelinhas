# ruff: noqa: F811
"""Suporte dos testes da 009: dois participantes no mesmo grupo e entregas em horários escolhidos."""

import pytest

from apps.fotos.tests.conftest import dono, parceiro  # noqa: F401
from apps.registros.tests.conftest import (  # noqa: F401
    AMBAR,
    SENHA,
    VERDE,
    Cliente,
    cliente,
    entregar,
    estranho,
    grupo_do_dono,
    logar,
    novo_grupo,
    novo_participante,
    pasta_de_fotos,
    relogio,
)


@pytest.fixture
def par(dono, parceiro):
    """(dono, parceiro) logados, no mesmo grupo."""
    return dono, parceiro()


def entregar_em(relogio, cliente, ano, mes, dia, hora=12, minuto=0, segundo=0, **corpo):
    """Entrega um registro com o relógio do servidor fixado (UTC)."""
    relogio.fixar(ano, mes, dia, hora, minuto, segundo)
    resposta = entregar(cliente, **corpo)
    assert resposta.status_code == 201, resposta.content
    return resposta.json()["id"]


def calendario(cliente, mes):
    return cliente.get("/api/v1/calendario", {"mes": mes})
