"""Fotos privadas (spec 004): manuscrito e perfil. O arquivo vive no volume privado; aqui só os metadados."""

import uuid

from django.conf import settings
from django.db import models


class Foto(models.Model):
    class Finalidade(models.TextChoices):
        MANUSCRITO = "manuscrito", "Manuscrito"
        PERFIL = "perfil", "Perfil"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="fotos"
    )
    finalidade = models.CharField(max_length=12, choices=Finalidade.choices)
    tipo = models.CharField(max_length=20)
    largura = models.PositiveIntegerField()
    altura = models.PositiveIntegerField()
    bytes = models.PositiveIntegerField()
    # Nome do arquivo dentro de FOTOS_DIR: sempre o UUID da foto com a extensão do tipo, nunca o nome enviado.
    arquivo = models.CharField(max_length=100)
    # Avulsa (False) ainda não pertence a registro nem ao perfil; a limpeza apaga as avulsas antigas.
    anexada = models.BooleanField(default=False)
    # Foto de manuscrito entregue num registro (spec 005): `PROTECT` porque registro entregue não se apaga.
    registro = models.ForeignKey(
        "registros.Registro", on_delete=models.PROTECT, null=True, blank=True, related_name="fotos"
    )
    ordem = models.PositiveSmallIntegerField(default=0)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["dono", "criada_em"], name="foto_dono_criada"),
            models.Index(fields=["anexada", "criada_em"], name="foto_anexada_criada"),
        ]

    def __str__(self):
        return f"Foto {self.finalidade} {self.id}"
