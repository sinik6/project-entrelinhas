"""Erros de negócio das fotos. As views traduzem `ErroLimite` em 429 e `ErroNaoEncontrado` em 404."""

from apps.acesso.erros import ErroDeNegocio


class ErroLimite(ErroDeNegocio):
    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ErroNaoEncontrado(ErroDeNegocio):
    """Não existe ou a pessoa não pode ver: a resposta é a mesma (Art. 13)."""

    mensagem = "Não encontrado."
