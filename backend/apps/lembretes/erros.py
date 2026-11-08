"""Erros de negócio dos lembretes."""

from apps.acesso.erros import ErroDeNegocio


class ErroIndisponivel(ErroDeNegocio):
    """Recurso não configurado neste ambiente (sem chaves VAPID). Vira 503."""

    mensagem = "Os lembretes não estão disponíveis."
