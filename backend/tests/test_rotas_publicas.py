from collections.abc import Iterator

from django.conf import settings
from django.urls import URLPattern, URLResolver
from rest_framework.permissions import AllowAny

import config.api_v1

# Única lista de rotas que podem responder sem login. Rota nova pública exige editar esta lista
# (e, portanto, passar por revisão).
ROTAS_PUBLICAS = {"health"}


def _rotas(padroes) -> Iterator[URLPattern]:
    for padrao in padroes:
        if isinstance(padrao, URLResolver):
            yield from _rotas(padrao.url_patterns)
        else:
            yield padrao


def test_nfr_sec_1_permissao_padrao_exige_autenticacao():
    """NFR-SEC-1 / CTL-5: sem declaração explícita, a rota exige autenticação."""
    padrao = settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"]

    assert padrao == ["rest_framework.permissions.IsAuthenticated"]


def test_prop_1_rotas_sem_login_estao_na_lista_publica():
    """PROP-1: toda rota da API que aceita requisição anônima consta em ROTAS_PUBLICAS."""
    abertas = set()
    for rota in _rotas(config.api_v1.urlpatterns):
        visao = getattr(rota.callback, "cls", None)
        assert visao is not None, f"rota {rota.name!r} não é uma view DRF"
        if not visao.permission_classes or AllowAny in visao.permission_classes:
            abertas.add(rota.name)

    assert abertas <= ROTAS_PUBLICAS, f"rotas abertas fora da lista: {abertas - ROTAS_PUBLICAS}"
