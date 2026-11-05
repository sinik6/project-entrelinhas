"""Grupo de escrita, perfil e convite (spec 003)."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Grupo(models.Model):
    """Espaço de escrita. O limite de membros é dado do grupo (Art. 13), não número fixo no código."""

    class Tipo(models.TextChoices):
        ESCRITA = "escrita", "Escrita"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.ESCRITA)
    limite_membros = models.PositiveSmallIntegerField(default=2)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(limite_membros__gte=1, limite_membros__lte=2),
                name="grupo_limite_entre_1_e_2",
            )
        ]

    def __str__(self):
        return f"Grupo {self.tipo} {self.id}"


class Perfil(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name="perfil"
    )
    nome = models.CharField(max_length=60)
    cor = models.CharField(max_length=7)
    grupo = models.ForeignKey(
        Grupo, on_delete=models.PROTECT, null=True, blank=True, related_name="perfis"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(cor__regex=r"^#[0-9A-F]{6}$"), name="perfil_cor_rrggbb"
            )
        ]

    def __str__(self):
        return self.nome


class Convite(models.Model):
    """Convite de uso único. O código nunca é guardado: só o SHA-256 dele."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="convites")
    criado_por = models.ForeignKey(
        Perfil, on_delete=models.CASCADE, related_name="convites_criados"
    )
    codigo_hash = models.CharField(max_length=64, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    usado_em = models.DateTimeField(null=True, blank=True)
    invalidado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["grupo"],
                condition=Q(usado_em__isnull=True, invalidado_em__isnull=True),
                name="um_convite_pendente_por_grupo",
            )
        ]

    def __str__(self):
        return f"Convite do grupo {self.grupo_id}"
