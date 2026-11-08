"""Rotas dos lembretes. Finas: chamam o serviço; 503 sem chaves VAPID."""

from rest_framework import status
from rest_framework.response import Response

from apps.fotos.views import ViewDeFotos

from . import services
from .erros import ErroIndisponivel


class ViewDeLembretes(ViewDeFotos):
    def handle_exception(self, exc):
        if isinstance(exc, ErroIndisponivel):
            return Response({"detalhe": exc.mensagem}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return super().handle_exception(exc)


class ChavePublicaView(ViewDeLembretes):
    def get(self, request):
        return Response({"chave": services.chave_publica()})


class AssinaturasView(ViewDeLembretes):
    def post(self, request):
        services.guardar(request.user, request.data)
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request):
        dados = request.data if isinstance(request.data, dict) else {}
        services.remover(request.user, dados.get("endpoint"))
        return Response(status=status.HTTP_204_NO_CONTENT)
