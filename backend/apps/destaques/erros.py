"""Erros de negócio dos destaques. A view traduz `ErroProibido` em 403."""

from apps.acesso.erros import ErroDeNegocio


class ErroProibido(ErroDeNegocio):
    """O objeto é visível ao grupo, mas é de outra pessoa."""

    mensagem = "Só quem escreveu pode fazer isso."
