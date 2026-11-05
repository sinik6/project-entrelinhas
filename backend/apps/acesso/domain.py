"""Regra de cor do perfil (spec 003, D-7): formato, legibilidade nos dois temas e diferença para a cor do parceiro.

Cálculo puro, sem banco. As constantes são calibráveis e ficam aqui.
"""

import math
import re

FUNDO_CLARO = "#FFFFFF"
FUNDO_ESCURO = "#121212"
CONTRASTE_MINIMO = 3.0
DIFERENCA_MINIMA = 25.0

_FORMATO = re.compile(r"#[0-9A-Fa-f]{6}")


class CorInvalida(ValueError):
    """A cor não está no formato `#RRGGBB`."""


def normalizar_cor(valor) -> str:
    if not isinstance(valor, str) or not _FORMATO.fullmatch(valor):
        raise CorInvalida("Use o formato #RRGGBB.")
    return valor.upper()


def _linear(canal: int) -> float:
    c = canal / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb_linear(cor: str) -> tuple[float, float, float]:
    return tuple(_linear(int(cor[i : i + 2], 16)) for i in (1, 3, 5))


def luminancia(cor: str) -> float:
    r, g, b = _rgb_linear(cor)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a: str, b: str) -> float:
    """Razão de contraste do WCAG entre duas cores `#RRGGBB`."""
    mais_clara, mais_escura = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (mais_clara + 0.05) / (mais_escura + 0.05)


def cor_legivel(cor: str) -> bool:
    """Contraste de pelo menos 3 para 1 com o fundo claro **e** com o escuro."""
    return (
        contraste(cor, FUNDO_CLARO) >= CONTRASTE_MINIMO
        and contraste(cor, FUNDO_ESCURO) >= CONTRASTE_MINIMO
    )


def _lab(cor: str) -> tuple[float, float, float]:
    r, g, b = _rgb_linear(cor)
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def diferenca(a: str, b: str) -> float:
    """Diferença de cor CIE76 (distância no espaço Lab)."""
    return math.dist(_lab(a), _lab(b))


def cores_distinguiveis(a: str, b: str) -> bool:
    return diferenca(a, b) >= DIFERENCA_MINIMA
