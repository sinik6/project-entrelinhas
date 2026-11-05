"""Rotas das fotos. Finas: validam o formato, chamam o serviço e traduzem os erros em HTTP."""

from django.http import FileResponse
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.acesso.services import perfil_para_dict
from apps.acesso.views import ViewDoAcesso

from . import servicos
from .erros import ErroLimite, ErroNaoEncontrado


class ViewDeFotos(ViewDoAcesso):
    def handle_exception(self, exc):
        if isinstance(exc, ErroLimite):
            return Response({"detalhe": exc.mensagem}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        if isinstance(exc, ErroNaoEncontrado):
            return Response({"detalhe": exc.mensagem}, status=status.HTTP_404_NOT_FOUND)
        return super().handle_exception(exc)


class EnviarView(ViewDeFotos):
    parser_classes = [MultiPartParser]

    def post(self, request):
        foto = servicos.enviar(
            request.user, request.FILES.get("arquivo"), str(request.data.get("finalidade", ""))
        )
        return Response(
            {
                "id": str(foto.id),
                "finalidade": foto.finalidade,
                "largura": foto.largura,
                "altura": foto.altura,
            },
            status=status.HTTP_201_CREATED,
        )


class FotoView(ViewDeFotos):
    def delete(self, request, foto_id):
        servicos.apagar_avulsa(request.user, foto_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ArquivoView(ViewDeFotos):
    def get(self, request, foto_id):
        foto = servicos.foto_visivel(request.user, foto_id)
        try:
            arquivo = servicos.caminho_do_arquivo(foto).open("rb")
        except FileNotFoundError:
            raise ErroNaoEncontrado from None
        resposta = FileResponse(arquivo, content_type=foto.tipo)
        resposta["Cache-Control"] = "private, no-store"
        resposta["X-Content-Type-Options"] = "nosniff"
        return resposta


class PerfilFotoView(ViewDeFotos):
    parser_classes = [JSONParser]

    def put(self, request):
        servicos.definir_foto_de_perfil(request.user, request.data.get("foto_id"))
        return Response(perfil_para_dict(request.user))

    def delete(self, request):
        servicos.remover_foto_de_perfil(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
