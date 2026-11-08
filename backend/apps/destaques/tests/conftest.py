# ruff: noqa: F811
"""Suporte dos testes da 007: registro entregue pela API e atalhos para destacar e comentar."""

import pytest

from apps.fotos.tests.conftest import apagar  # noqa: F401
from apps.registros.tests.conftest import (  # noqa: F401
    AMBAR,
    SENHA,
    VERDE,
    Cliente,
    cliente,
    dono,
    entregar,
    estranho,
    grupo_do_dono,
    logar,
    marcadores,
    novo_grupo,
    novo_participante,
    parceiro,
    pasta_de_fotos,
    relogio,
)

TEXTO = "Primeira frase do dia. Segunda frase do dia."


def registro_de(autor, texto=TEXTO, visibilidade="full", trecho=None) -> str:
    resposta = entregar(autor, texto=texto, visibilidade=visibilidade, trecho=trecho)
    assert resposta.status_code == 201, resposta.content
    return resposta.json()["id"]


def destacar(cliente, registro_id, inicio, fim, comentario=None):
    corpo = {"inicio": inicio, "fim": fim}
    if comentario is not None:
        corpo["comentario"] = comentario
    return cliente.postar(f"/api/v1/registros/{registro_id}/destaques", corpo)


def comentar(cliente, destaque_id, texto):
    return cliente.postar(f"/api/v1/destaques/{destaque_id}/comentarios", {"texto": texto})


def listar(cliente, registro_id):
    return cliente.get(f"/api/v1/registros/{registro_id}/destaques")


@pytest.fixture
def par(dono, parceiro):
    """(dono, parceiro) logados, no mesmo grupo."""
    return dono, parceiro()
