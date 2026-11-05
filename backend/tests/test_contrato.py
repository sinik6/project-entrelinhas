"""O contrato escrito à mão (`specs/changes/*/contracts/openapi.yaml`) e as rotas reais não podem divergir."""

import re
from pathlib import Path

import pytest
from django.urls import URLResolver

import config.api_v1

RAIZ = Path(__file__).resolve().parents[2]


def _rotas(padroes):
    for padrao in padroes:
        if isinstance(padrao, URLResolver):
            yield from _rotas(padrao.url_patterns)
        else:
            # `fotos/<str:foto_id>` (Django) e `/fotos/{id}` (OpenAPI) viram a mesma forma: `/fotos/{}`.
            yield re.sub(r"<[^>]+>", "{}", "/" + str(padrao.pattern))


def _caminhos_dos_contratos() -> set[str]:
    caminhos = set()
    for arquivo in RAIZ.glob("specs/changes/*/contracts/openapi.yaml"):
        texto = arquivo.read_text(encoding="utf-8")
        # Contrato de mudança ainda não implementada: `x-estado: planejado` em `info`; sai quando a rota entra no código.
        if re.search(r"^  x-estado: planejado\s*$", texto, re.M):
            continue
        caminhos |= {
            re.sub(r"\{[^}]+\}", "{}", c) for c in re.findall(r"^  (/[\w/.{}-]*):\s*$", texto, re.M)
        }
    return caminhos


def test_ctl_18_o_contrato_cobre_todas_as_rotas_e_so_elas():
    """[003] CTL-18: toda rota da API está no contrato, e nenhuma rota do contrato deixou de existir."""
    contratos = _caminhos_dos_contratos()
    if not contratos:
        pytest.skip("nenhum contrato em specs/changes (a mudança foi arquivada)")

    reais = set(_rotas(config.api_v1.urlpatterns))

    assert reais == contratos, (
        f"só nas rotas: {reais - contratos}; só no contrato: {contratos - reais}"
    )
