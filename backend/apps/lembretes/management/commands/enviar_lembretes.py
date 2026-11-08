"""Uma execução do disparador (para teste e uso manual): `manage.py enviar_lembretes [--agora 2026-11-05T21:30:00-03:00]`."""

from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.lembretes.disparador import enviar_lembretes
from apps.lembretes.envio import enviar_web_push


class Command(BaseCommand):
    help = "Envia o lembrete diário uma vez, como se fosse a hora dada (com fuso)."

    def add_arguments(self, parser):
        parser.add_argument("--agora", help="Instante ISO com fuso; padrão: agora.")

    def handle(self, *args, **opcoes):
        if opcoes["agora"]:
            try:
                agora = datetime.fromisoformat(opcoes["agora"])
            except ValueError:
                raise CommandError("--agora precisa ser uma data ISO.") from None
            if agora.tzinfo is None:
                raise CommandError(
                    "--agora precisa ter fuso (ex.: -03:00); sem ele a hora é ambígua."
                )
        else:
            agora = timezone.now()
        r = enviar_lembretes(agora, enviar_web_push)
        self.stdout.write(
            f"enviados={r['enviados']} removidos={r['removidos']} "
            f"falhas={r['falhas']} pessoas={r['pessoas']}"
        )
