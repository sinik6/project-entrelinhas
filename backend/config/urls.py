"""Rotas raiz: API v1 e Django Admin.

O Admin ganha o prefixo público da VPS (`DJANGO_PREFIXO_URL`): /entrelinhas/admin/ lá,
/admin/ no desenvolvimento. A API não tem prefixo: só o BFF a chama, pela rede interna.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(f"{settings.PREFIXO_ROTAS}admin/", admin.site.urls),
    path("api/v1/", include("config.api_v1")),
]
