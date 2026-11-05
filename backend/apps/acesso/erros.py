"""Erros de negócio do acesso. Os services levantam estes; as views os traduzem em resposta HTTP."""


class ErroDeNegocio(Exception):
    pass


class ErroGenerico(ErroDeNegocio):
    """Falha que não pode dizer o motivo (login e convite). Vira 400 com a mensagem única."""

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ErroConflito(ErroDeNegocio):
    """O estado atual impede a ação (já tem grupo, grupo cheio). Vira 409."""

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ErroValidacao(ErroDeNegocio):
    """Campos inválidos. Vira 422 com `{"campos": {campo: [mensagens]}}`."""

    def __init__(self, campos: dict[str, list[str]]):
        super().__init__(str(campos))
        self.campos = campos
