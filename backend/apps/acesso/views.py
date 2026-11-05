"""Rotas do acesso. Finas: validam o formato, chamam o service e traduzem os erros de negócio em HTTP."""

from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .erros import ErroConflito, ErroDeNegocio, ErroGenerico, ErroValidacao
from .serializers import (
    AceitarConviteSerializer,
    EntrarSerializer,
    PerfilSerializer,
    SenhaSerializer,
)


def _dados_validos(serializer_class, dados) -> dict:
    serializer = serializer_class(data=dados)
    if not serializer.is_valid():
        raise ErroValidacao(
            {campo: [str(m) for m in mensagens] for campo, mensagens in serializer.errors.items()}
        )
    return serializer.validated_data


class ViewDoAcesso(APIView):
    """Traduz `ErroDeNegocio` em resposta: 400 única, 409 de conflito e 422 por campo."""

    def handle_exception(self, exc):
        if isinstance(exc, ErroValidacao):
            return Response({"campos": exc.campos}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        if isinstance(exc, ErroGenerico):
            return Response({"detalhe": exc.mensagem}, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(exc, ErroConflito):
            return Response({"detalhe": exc.mensagem}, status=status.HTTP_409_CONFLICT)
        if isinstance(exc, ErroDeNegocio):  # pragma: no cover - toda subclasse acima já foi tratada
            raise exc
        return super().handle_exception(exc)


class CsrfView(ViewDoAcesso):
    """Entrega o token de proteção no corpo; o segredo vai num cookie que o script não lê (D-2)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"token": get_token(request._request)})


class EntrarView(ViewDoAcesso):
    permission_classes = [AllowAny]

    def post(self, request):
        dados = _dados_validos(EntrarSerializer, request.data)
        usuario = services.entrar(request._request, dados["email"], dados["senha"])
        return Response(services.perfil_para_dict(usuario))


class SairView(ViewDoAcesso):
    def post(self, request):
        services.sair(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PerfilView(ViewDoAcesso):
    def get(self, request):
        return Response(services.perfil_para_dict(request.user))

    def patch(self, request):
        dados = _dados_validos(PerfilSerializer, request.data)
        return Response(
            services.atualizar_perfil(request.user, dados.get("nome"), dados.get("cor"))
        )


class SenhaView(ViewDoAcesso):
    def post(self, request):
        dados = _dados_validos(SenhaSerializer, request.data)
        services.trocar_senha(
            request._request, request.user, dados["senha_atual"], dados["senha_nova"]
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class GrupoView(ViewDoAcesso):
    def get(self, request):
        return Response({"grupo": services.grupo_de(request.user)})

    def post(self, request):
        return Response(services.criar_grupo(request.user), status=status.HTTP_201_CREATED)


class ConviteGerarView(ViewDoAcesso):
    def post(self, request):
        codigo, expira_em = services.gerar_convite(request.user)
        return Response({"codigo": codigo, "expira_em": expira_em}, status=status.HTTP_201_CREATED)


class ConviteAceitarView(ViewDoAcesso):
    permission_classes = [AllowAny]

    def post(self, request):
        dados = _dados_validos(AceitarConviteSerializer, request.data)
        usuario = services.aceitar_convite(
            request._request,
            dados["codigo"],
            dados["nome"],
            dados["email"],
            dados["senha"],
            dados["cor"],
        )
        return Response(services.perfil_para_dict(usuario), status=status.HTTP_201_CREATED)
