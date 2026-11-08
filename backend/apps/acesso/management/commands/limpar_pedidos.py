"""Apaga os pedidos de recuperação de senha com mais de 24 horas (retenção da spec 011). Roda no deploy."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.acesso.models import PedidoRecuperacao


class Command(BaseCommand):
    help = "Apaga os pedidos de recuperação de senha com mais de 24 horas."

    def handle(self, *args, **opcoes):
        apagados, _ = PedidoRecuperacao.objects.filter(
            criado_em__lt=timezone.now() - timedelta(hours=24)
        ).delete()
        self.stdout.write(f"pedidos apagados: {apagados}")
