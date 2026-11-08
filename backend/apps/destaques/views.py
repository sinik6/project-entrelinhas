"""Rotas dos destaques. Finas: chamam o serviço; 403 para o que é de outra pessoa."""

from rest_framework import status
from rest_framework.response import Response

from apps.fotos.views import ViewDeFotos

from . import services
from .erros import ErroProibido


class ViewDeDestaques(ViewDeFotos):
    def handle_exception(self, exc):
        if isinstance(exc, ErroProibido):
            return Response({"detalhe": exc.mensagem}, status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)


def _dados(request) -> dict:
    return request.data if isinstance(request.data, dict) else {}


class DestaquesDoRegistroView(ViewDeDestaques):
    def get(self, request, registro_id):
        return Response(services.listar(request.user, registro_id))

    def post(self, request, registro_id):
        dados = _dados(request)
        criado = services.criar(
            request.user,
            registro_id,
            dados.get("inicio"),
            dados.get("fim"),
            dados.get("comentario"),
        )
        return Response(criado, status=status.HTTP_201_CREATED)


class DestaqueView(ViewDeDestaques):
    def delete(self, request, destaque_id):
        services.apagar_destaque(request.user, destaque_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ComentariosView(ViewDeDestaques):
    def post(self, request, destaque_id):
        comentario = services.comentar(request.user, destaque_id, _dados(request).get("texto"))
        return Response(comentario, status=status.HTTP_201_CREATED)


class ComentarioView(ViewDeDestaques):
    def patch(self, request, comentario_id):
        return Response(
            services.editar_comentario(request.user, comentario_id, _dados(request).get("texto"))
        )

    def delete(self, request, comentario_id):
        services.apagar_comentario(request.user, comentario_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
