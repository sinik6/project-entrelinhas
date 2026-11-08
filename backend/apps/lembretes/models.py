"""Assinaturas de Web Push e o registro de envio do dia (spec 010)."""

import uuid

from django.conf import settings
from django.db import models


class AssinaturaPush(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assinaturas_push"
    )
    # Endereço do serviço de push (só de hosts da lista fixa, ver `destinos.py`) e as chaves do navegador.
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=128)
    auth = models.CharField(max_length=64)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"assinatura {self.pk}"


class LembreteEnviado(models.Model):
    """Uma linha por pessoa por dia, gravada ANTES do envio: garante no máximo um aviso (REQ-19.3)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lembretes_enviados"
    )
    data = models.DateField()
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "data"], name="um_lembrete_por_pessoa_por_dia"
            )
        ]

    def __str__(self):
        return f"lembrete {self.usuario_id} {self.data}"
