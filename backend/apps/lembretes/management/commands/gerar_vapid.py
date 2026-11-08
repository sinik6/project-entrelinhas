"""Gera um par de chaves VAPID e o IMPRIME (não grava). A privada vai só para o segredo do GitHub, nunca para o chat nem para o git."""

import base64

from cryptography.hazmat.primitives import serialization
from django.core.management.base import BaseCommand
from py_vapid import Vapid


def _b64url(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


class Command(BaseCommand):
    help = "Imprime VAPID_PUBLIC_KEY e VAPID_PRIVATE_KEY (base64url)."

    def handle(self, *args, **opcoes):
        chave = Vapid()
        chave.generate_keys()
        publica = chave.public_key.public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
        )
        privada = chave.private_key.private_numbers().private_value.to_bytes(32, "big")
        self.stdout.write(f"VAPID_PUBLIC_KEY={_b64url(publica)}")
        self.stdout.write(f"VAPID_PRIVATE_KEY={_b64url(privada)}")
        self.stderr.write(
            "Guarde a chave privada só nos segredos do GitHub (VAPID_PRIVATE_KEY). "
            "Ela não deve ir ao chat nem ao git."
        )
