"""O envio real de um Web Push (spec 010, ADR-0012). Único arquivo que fala com a biblioteca `pywebpush`.

Resultados: `ok`, `gone` (404 ou 410: a assinatura não existe mais) e `falha` (qualquer outra coisa). Nada de endereço, chave
nem mensagem de erro da biblioteca vai ao log: a chave privada poderia estar nela.
"""

import logging

import requests
from django.conf import settings
from pywebpush import WebPushException, webpush

from .destinos import endpoint_permitido

log = logging.getLogger("apps.lembretes")
TEMPO_LIMITE = 10  # segundos


def enviar_web_push(assinatura, carga: str) -> str:
    if not endpoint_permitido(assinatura.endpoint):
        # Defesa em profundidade: a lista vale também na hora de enviar, mesmo que o banco tenha sido adulterado.
        log.warning("envio recusado: destino fora da lista")
        return "falha"
    try:
        webpush(
            subscription_info={
                "endpoint": assinatura.endpoint,
                "keys": {"p256dh": assinatura.p256dh, "auth": assinatura.auth},
            },
            data=carga,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            # um dicionário novo a cada envio: a biblioteca o altera
            vapid_claims={"sub": settings.VAPID_ASSUNTO},
            timeout=TEMPO_LIMITE,
        )
        return "ok"
    except WebPushException as erro:
        status = getattr(getattr(erro, "response", None), "status_code", None)
        if status in (404, 410):
            return "gone"
        log.warning("envio falhou status=%s", status)
        return "falha"
    except (requests.RequestException, OSError, ValueError) as erro:
        log.warning("envio falhou tipo=%s", type(erro).__name__)
        return "falha"
