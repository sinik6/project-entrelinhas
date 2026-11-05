"""Apaga as fotos avulsas (nunca anexadas) criadas há mais de 24 horas. Roda no deploy (spec 004, REQ-6.9)."""

from django.core.management.base import BaseCommand

from apps.fotos import servicos


class Command(BaseCommand):
    help = "Apaga as fotos avulsas com mais de 24 horas."

    def handle(self, *args, **opcoes):
        total = servicos.limpar_avulsas_antigas()
        self.stdout.write(f"Fotos avulsas apagadas: {total}")
