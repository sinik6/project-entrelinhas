"""Rotas dos registros. Finas: chamam o serviço; só `GET` e `POST` existem (o resto responde 405)."""

from rest_framework import status
from rest_framework.response import Response

from apps.fotos.views import ViewDeFotos

from . import services


class RegistrosView(ViewDeFotos):
    def get(self, request):
        return Response(services.listar_mes(request.user, request.query_params.get("mes")))

    def post(self, request):
        dados = request.data if isinstance(request.data, dict) else {}
        registro = services.entregar(
            request.user,
            dados.get("texto"),
            dados.get("visibilidade"),
            dados.get("trecho"),
            dados.get("fotos"),
        )
        return Response(registro, status=status.HTTP_201_CREATED)


class RegistroView(ViewDeFotos):
    def get(self, request, registro_id):
        return Response(services.ler(request.user, registro_id))
