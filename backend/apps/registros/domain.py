"""A regra de visibilidade do registro (spec 005, Art. 12). Este é o ÚNICO arquivo do app que lê o texto do registro.

Tudo o que a API devolve sobre um registro passa por `visivel_para`. Quem não é o autor recebe a visão do parceiro
(deny-by-default): nunca o texto inteiro, nunca o trecho em offsets, nunca fotos fora do `full`.
"""

import unicodedata

from apps.acesso.erros import ErroValidacao

TEXTO_MINIMO = 10  # caracteres úteis (sem contar espaços e quebras nas pontas)
TEXTO_MAXIMO = 20_000
VISIBILIDADES = ("full", "private", "partial")
AVISO_PRIVADO = "Enviado, mas mantido privado pelo autor"
_PERMITIDOS = ("\n", "\t")


def validar_texto(texto) -> str:
    """Devolve o texto como veio; recusa o que não é texto válido. A mensagem nunca repete o texto."""
    if not isinstance(texto, str):
        raise ErroValidacao({"texto": ["Escreva o texto do dia."]})
    if len(texto.strip()) < TEXTO_MINIMO:
        raise ErroValidacao({"texto": [f"Escreva pelo menos {TEXTO_MINIMO} caracteres."]})
    if len(texto) > TEXTO_MAXIMO:
        raise ErroValidacao({"texto": [f"Use no máximo {TEXTO_MAXIMO} caracteres."]})
    for caractere in texto:
        categoria = unicodedata.category(caractere)
        if (categoria == "Cc" and caractere not in _PERMITIDOS) or categoria == "Cs":
            raise ErroValidacao({"texto": ["O texto tem caracteres que não podem ser usados."]})
    return texto


def _inteiro(valor) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_visibilidade_e_trecho(visibilidade, trecho, texto: str) -> tuple[int, int] | None:
    """`partial` exige `{inicio, fim}` com 0 <= inicio < fim <= tamanho do texto (pontos de código); os outros recusam trecho."""
    if not isinstance(visibilidade, str) or visibilidade not in VISIBILIDADES:
        raise ErroValidacao(
            {"visibilidade": ["Escolha quem pode ler: todos, só você ou um trecho."]}
        )
    if visibilidade != "partial":
        if trecho is not None:
            raise ErroValidacao(
                {"trecho": ["Só informe o trecho quando escolher mostrar um trecho."]}
            )
        return None
    if (
        not isinstance(trecho, dict)
        or not _inteiro(trecho.get("inicio"))
        or not _inteiro(trecho.get("fim"))
    ):
        raise ErroValidacao({"trecho": ["Escolha o trecho que a outra pessoa poderá ler."]})
    inicio, fim = trecho["inicio"], trecho["fim"]
    if not 0 <= inicio < fim <= len(texto):
        raise ErroValidacao(
            {"trecho": ["O trecho precisa ser um pedaço do texto, com pelo menos um caractere."]}
        )
    return inicio, fim


def fatia(texto: str, inicio: int, fim: int) -> str:
    """Pontos de código, como o Python indexa a `str` (ADR-0009)."""
    return texto[inicio:fim]


def texto_visivel_para(registro, usuario_id) -> str | None:
    """O texto que a pessoa pode ler do registro, ou `None`. É a ÚNICA porta de outros apps ao texto (spec 007).

    Em `full` é o texto todo; em `partial`, só o trecho (para todos, inclusive o autor: os offsets dos destaques são
    relativos a ele, ADR-0009); em `private` não há texto para ninguém aqui.
    """
    if registro.visibilidade == "full":
        return registro.texto
    if registro.visibilidade == "partial":
        return fatia(registro.texto, registro.trecho_inicio, registro.trecho_fim)
    return None


def _iso(valor):
    return valor.isoformat() if hasattr(valor, "isoformat") else valor


def visivel_para(registro, usuario_id, autor: dict, fotos: list[str]) -> dict:
    """O que `usuario_id` pode saber do registro. `autor` é {nome, cor, foto_url}; `fotos` são os ids, em ordem."""
    base = {
        "id": str(registro.id),
        "data": _iso(registro.data),
        "entregue_em": _iso(registro.entregue_em),
        "autor": autor,
    }
    if registro.autor_id == usuario_id:
        trecho = (
            {"inicio": registro.trecho_inicio, "fim": registro.trecho_fim}
            if registro.visibilidade == "partial"
            else None
        )
        return {
            **base,
            "visibilidade": registro.visibilidade,
            "trecho": trecho,
            "texto": registro.texto,
            "fotos": list(fotos),
            "meu": True,
        }
    # Parceiro: só o texto visível; nada de offsets, de tamanho do texto inteiro nem de fotos fora do `full`.
    if registro.visibilidade == "full":
        texto_visivel, fotos_visiveis, aviso = registro.texto, list(fotos), None
    elif registro.visibilidade == "partial":
        texto_visivel = fatia(registro.texto, registro.trecho_inicio, registro.trecho_fim)
        fotos_visiveis, aviso = [], None
    else:
        texto_visivel, fotos_visiveis, aviso = None, [], AVISO_PRIVADO
    visao = {
        **base,
        "visibilidade_efetiva": registro.visibilidade,
        "texto_visivel": texto_visivel,
        "fotos": fotos_visiveis,
        "meu": False,
    }
    if aviso:
        visao["aviso"] = aviso
    return visao
