"""Registro diário (spec 005): o texto e a visibilidade escolhida. Quem pode ler o quê é decidido só em `domain.visivel_para`."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Registro(models.Model):
    class Visibilidade(models.TextChoices):
        FULL = "full", "Todo o grupo lê"
        PRIVATE = "private", "Só o autor"
        PARTIAL = "partial", "Só um trecho"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grupo = models.ForeignKey("acesso.Grupo", on_delete=models.PROTECT, related_name="registros")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="registros"
    )
    # Dia da entrega em America/Sao_Paulo (a regra de um registro por pessoa por dia vale sobre ele).
    data = models.DateField()
    # Guardado como veio, sem normalização (ADR-0009): os offsets são em pontos de código deste texto.
    texto = models.TextField()
    visibilidade = models.CharField(max_length=8, choices=Visibilidade.choices)
    trecho_inicio = models.PositiveIntegerField(null=True, blank=True)
    trecho_fim = models.PositiveIntegerField(null=True, blank=True)
    entregue_em = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["autor", "data"], name="um_registro_por_autor_por_dia"),
            models.CheckConstraint(
                condition=(
                    Q(
                        visibilidade="partial",
                        trecho_inicio__isnull=False,
                        trecho_fim__isnull=False,
                        trecho_fim__gt=F("trecho_inicio"),
                    )
                    | (
                        ~Q(visibilidade="partial")
                        & Q(trecho_inicio__isnull=True, trecho_fim__isnull=True)
                    )
                ),
                name="registro_trecho_so_em_partial",
            ),
        ]
        indexes = [models.Index(fields=["grupo", "data"], name="registro_grupo_data")]

    def __str__(self):
        return f"Registro {self.id} ({self.data})"
