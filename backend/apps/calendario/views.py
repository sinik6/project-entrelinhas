"""Rota do calendário. Fina: chama o serviço."""

from rest_framework.response import Response

from apps.acesso.views import ViewDoAcesso

from . import services


class CalendarioView(ViewDoAcesso):
    def get(self, request):
        return Response(services.calendario(request.user, request.query_params.get("mes")))
