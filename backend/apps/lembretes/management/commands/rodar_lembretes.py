"""O laço do serviço `entrelinhas-lembretes`: a cada ciclo marca o batimento (a saúde do contêiner lê a idade dele) e roda o disparador."""

import logging
import time as relogio

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.lembretes.disparador import enviar_lembretes, limpar_marcas_antigas
from apps.lembretes.envio import enviar_web_push

log = logging.getLogger("apps.lembretes")


class Command(BaseCommand):
    help = "Laço do disparador de lembretes."

    def add_arguments(self, parser):
        parser.add_argument("--intervalo", type=float, default=30.0, help="Segundos entre ciclos.")
        parser.add_argument("--ciclos", type=int, default=0, help="0 = para sempre (uso real).")

    def handle(self, *args, **opcoes):
        ciclo = 0
        ultima_limpeza = None
        while True:
            ciclo += 1
            agora = timezone.now()
            try:
                settings.LEMBRETES_BATIMENTO.parent.mkdir(parents=True, exist_ok=True)
                settings.LEMBRETES_BATIMENTO.touch()
                enviar_lembretes(agora, enviar_web_push)
                if ultima_limpeza != agora.date():
                    limpar_marcas_antigas(agora.date())
                    ultima_limpeza = agora.date()
            except Exception as erro:
                log.error("ciclo do disparador falhou tipo=%s", type(erro).__name__)
            if opcoes["ciclos"] and ciclo >= opcoes["ciclos"]:
                return
            relogio.sleep(opcoes["intervalo"])
