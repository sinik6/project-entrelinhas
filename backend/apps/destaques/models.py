"""Destaque e comentário (spec 007). O texto destacado NÃO é guardado: sai do texto visível pelas posições."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Destaque(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registro = models.ForeignKey(
        "registros.Registro", on_delete=models.CASCADE, related_name="destaques"
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="destaques"
    )
    # Pontos de código do TEXTO VISÍVEL do registro (ADR-0009), [inicio, fim).
    inicio = models.PositiveIntegerField()
    fim = models.PositiveIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(fim__gt=F("inicio")), name="destaque_fim_apos_inicio"
            )
        ]
        indexes = [models.Index(fields=["registro", "autor"], name="destaque_registro_autor")]
        ordering = ["criado_em", "id"]

    def __str__(self):
        return f"destaque {self.pk}"


class Comentario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destaque = models.ForeignKey(Destaque, on_delete=models.CASCADE, related_name="comentarios")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios"
    )
    texto = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    editado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["destaque", "criado_em"], name="comentario_destaque_data")]
        ordering = ["criado_em", "id"]

    def __str__(self):
        return f"comentário {self.pk}"
