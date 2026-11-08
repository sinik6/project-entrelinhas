"""Roteador da API v1: cada app de domínio registra suas rotas aqui."""

from django.urls import include, path

urlpatterns = [
    path("", include("apps.common.urls")),
    path("", include("apps.acesso.urls")),
    path("", include("apps.fotos.urls")),
    path("", include("apps.registros.urls")),
    path("", include("apps.destaques.urls")),
    path("", include("apps.calendario.urls")),
    path("", include("apps.lembretes.urls")),
]
