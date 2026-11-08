"""Casos de uso das assinaturas (spec 010). Não importa DRF."""

import base64
import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from apps.acesso.erros import ErroConflito, ErroValidacao
from apps.fotos.erros import ErroNaoEncontrado

from .destinos import endpoint_permitido
from .erros import ErroIndisponivel
from .models import AssinaturaPush

log = logging.getLogger("apps.lembretes")
APARELHOS_POR_PESSOA = 5
BASE64URL = re.compile(r"[A-Za-z0-9_-]+")


def _bytes(valor) -> bytes | None:
    if not isinstance(valor, str) or not BASE64URL.fullmatch(valor):
        return None
    try:
        return base64.urlsafe_b64decode(valor + "=" * (-len(valor) % 4))
    except ValueError:
        return None


def _validar(dados) -> tuple[str, str, str]:
    if not isinstance(dados, dict):
        raise ErroValidacao({"endpoint": ["Informe a assinatura."]})
    endpoint = dados.get("endpoint")
    if not endpoint_permitido(endpoint):
        raise ErroValidacao({"endpoint": ["Esse endereço de aviso não é aceito."]})
    chaves = dados.get("keys")
    if not isinstance(chaves, dict):
        raise ErroValidacao({"keys": ["Informe as chaves da assinatura."]})
    p256dh, auth = _bytes(chaves.get("p256dh")), _bytes(chaves.get("auth"))
    if p256dh is None or len(p256dh) != 65 or p256dh[0] != 4:
        raise ErroValidacao({"keys": ["Chave da assinatura inválida."]})
    if auth is None or len(auth) != 16:
        raise ErroValidacao({"keys": ["Chave da assinatura inválida."]})
    return endpoint, chaves["p256dh"], chaves["auth"]


def chave_publica() -> str:
    chave = getattr(settings, "VAPID_PUBLIC_KEY", "")
    if not chave:
        raise ErroIndisponivel
    return chave


def guardar(usuario, dados) -> None:
    endpoint, p256dh, auth = _validar(dados)
    with transaction.atomic():
        # Travar o usuário serializa os pedidos dele: o limite de 5 vale também para pedidos simultâneos.
        get_user_model().objects.select_for_update().get(pk=usuario.pk)
        existente = AssinaturaPush.objects.select_for_update().filter(endpoint=endpoint).first()
        if existente is not None and existente.usuario_id == usuario.pk:
            existente.p256dh, existente.auth = p256dh, auth
            existente.save(update_fields=["p256dh", "auth"])
            return
        if AssinaturaPush.objects.filter(usuario=usuario).count() >= APARELHOS_POR_PESSOA:
            raise ErroConflito(f"Você já tem {APARELHOS_POR_PESSOA} aparelhos com lembrete.")
        if (
            existente is not None
        ):  # o mesmo navegador entrou com outra conta: a assinatura passa para esta
            existente.usuario, existente.p256dh, existente.auth = usuario, p256dh, auth
            existente.save(update_fields=["usuario", "p256dh", "auth"])
            return
        try:
            with transaction.atomic():
                AssinaturaPush.objects.create(
                    usuario=usuario, endpoint=endpoint, p256dh=p256dh, auth=auth
                )
        except (
            IntegrityError
        ):  # outra requisição inseriu o mesmo endereço agora: tenta como atualização
            AssinaturaPush.objects.filter(endpoint=endpoint).update(
                usuario=usuario, p256dh=p256dh, auth=auth
            )
    log.info("assinatura guardada usuario=%s", usuario.pk)


def remover(usuario, endpoint) -> None:
    if not isinstance(endpoint, str):
        raise ErroNaoEncontrado
    apagadas, _ = AssinaturaPush.objects.filter(usuario=usuario, endpoint=endpoint).delete()
    if not apagadas:
        raise ErroNaoEncontrado
    log.info("assinatura removida usuario=%s", usuario.pk)
