"""Roteador da API v1: cada app de domínio registra suas rotas aqui."""

from django.urls import include, path

urlpatterns = [
    path("", include("apps.common.urls")),
]
