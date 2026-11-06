"""[005] A função única `visivel_para` e as propriedades PROP-6 e PROP-7 (sem banco: só a regra)."""

import json
import random
from types import SimpleNamespace

import pytest

from apps.acesso.erros import ErroValidacao
from apps.registros import domain

from .conftest import marcadores

AUTOR_ID, PARCEIRO_ID = 1, 2
AUTOR = {"nome": "Ana", "cor": "#4D7C0F", "foto_url": None}
FOTOS = ["f1", "f2"]


def registro(texto, visibilidade="full", inicio=None, fim=None):
    return SimpleNamespace(
        id="r1",
        data="2026-11-05",
        entregue_em="2026-11-05T12:00:00Z",
        autor_id=AUTOR_ID,
        texto=texto,
        visibilidade=visibilidade,
        trecho_inicio=inicio,
        trecho_fim=fim,
    )


def ver(reg, usuario_id):
    return domain.visivel_para(reg, usuario_id, AUTOR, FOTOS)


def test_req_9_1_autor_ve_tudo_do_proprio_registro():
    """[005] REQ-9.1: texto inteiro, visibilidade, trecho, fotos e quem é."""
    visto = ver(registro("abcdefghij", "partial", 2, 5), AUTOR_ID)

    assert visto["meu"] is True
    assert visto["texto"] == "abcdefghij"
    assert visto["visibilidade"] == "partial"
    assert visto["trecho"] == {"inicio": 2, "fim": 5}
    assert visto["fotos"] == FOTOS
    assert visto["autor"] == AUTOR


def test_req_9_2_parceiro_ve_o_texto_inteiro_e_as_fotos_em_full():
    """[005] REQ-9.2."""
    visto = ver(registro("abcdefghij"), PARCEIRO_ID)

    assert visto["meu"] is False
    assert visto["visibilidade_efetiva"] == "full"
    assert visto["texto_visivel"] == "abcdefghij"
    assert visto["fotos"] == FOTOS
    assert "texto" not in visto
    assert "trecho" not in visto


def test_req_9_3_parceiro_so_ve_o_trecho_e_nenhuma_foto_em_partial():
    """[005] REQ-9.3: só o trecho, sem fotos, sem o texto fora dele e sem os offsets."""
    visto = ver(registro("0123456789", "partial", 3, 6), PARCEIRO_ID)

    assert visto["visibilidade_efetiva"] == "partial"
    assert visto["texto_visivel"] == "345"
    assert visto["fotos"] == []
    assert "texto" not in visto
    assert "trecho" not in visto
    assert "visibilidade" not in visto
    for chave in ("inicio", "fim", "trecho"):
        assert chave not in json.dumps(visto)


def test_req_9_4_parceiro_so_ve_a_indicacao_de_entrega_em_private():
    """[005] REQ-9.4."""
    visto = ver(registro("segredo do autor", "private"), PARCEIRO_ID)

    assert visto["visibilidade_efetiva"] == "private"
    assert visto["texto_visivel"] is None
    assert visto["fotos"] == []
    assert visto["aviso"] == "Enviado, mas mantido privado pelo autor"
    assert "segredo" not in json.dumps(visto)


def test_nfr_reg_1_dois_participantes_quaisquer_diferentes_do_autor_sao_parceiros():
    """[005] NFR-REG-1: quem não é o autor recebe sempre a visão do parceiro (deny-by-default)."""
    assert ver(registro("abcdefghij", "private"), 99)["meu"] is False


def test_prop_6_nada_fora_do_texto_visivel_aparece_na_resposta_do_parceiro():
    """[005] PROP-6: com marcadores únicos, o JSON do parceiro só tem os marcadores do trecho."""
    azar = random.Random(20261105)
    for _ in range(200):
        quantos = azar.randint(2, 30)
        tokens = marcadores(quantos)
        texto = "".join(tokens)
        visibilidade = azar.choice(["full", "private", "partial"])
        inicio = azar.randrange(0, quantos)
        fim = azar.randint(inicio + 1, quantos)
        reg = registro(
            texto,
            visibilidade,
            inicio * 5 if visibilidade == "partial" else None,
            fim * 5 if visibilidade == "partial" else None,
        )

        saida = json.dumps(ver(reg, PARCEIRO_ID), ensure_ascii=False)

        if visibilidade == "full":
            dentro = set(tokens)
        elif visibilidade == "partial":
            dentro = set(tokens[inicio:fim])
        else:
            dentro = set()
        for token in tokens:
            assert (token in saida) == (token in dentro), (visibilidade, inicio, fim, token)


@pytest.mark.parametrize(
    "texto",
    [
        "simples ascii com acentuação: ção, ñ, é",
        "emoji 😀👍🏽 e bandeira 🇧🇷 no meio",
        "é acento composto (e + acento) separado",
        "linhas\nquebradas\ne\ttabulação\n",
        "日本語のテキストと混ざった text",
    ],
)
def test_prop_7_texto_visivel_e_a_fatia_em_pontos_de_codigo(texto):
    """[005] PROP-7: para qualquer trecho válido, texto_visivel == texto[inicio:fim] em pontos de código."""
    azar = random.Random(7)
    total = len(texto)
    for _ in range(100):
        inicio = azar.randrange(0, total)
        fim = azar.randint(inicio + 1, total)

        visto = ver(registro(texto, "partial", inicio, fim), PARCEIRO_ID)

        assert visto["texto_visivel"] == texto[inicio:fim]


def test_prop_7_emoji_conta_como_um_ponto_de_codigo_e_nao_dois():
    """[005] PROP-7 / ADR-0009: a unidade é o ponto de código, não a unidade UTF-16 do JavaScript."""
    texto = "a😀b"
    assert len(texto) == 3
    assert ver(registro(texto, "partial", 1, 2), PARCEIRO_ID)["texto_visivel"] == "😀"


# ---------- validações de domínio (REQ-8.3, REQ-8.4) ----------


def test_req_8_3_texto_aceito_no_limite_de_10_e_de_20000():
    """[005] REQ-8.3: 10 caracteres úteis é o mínimo; 20 000 é o máximo."""
    assert domain.validar_texto("a" * 10) == "a" * 10
    assert domain.validar_texto("  " + "a" * 10 + "  ") == "  " + "a" * 10 + "  "
    assert domain.validar_texto("a" * 20000)


@pytest.mark.parametrize(
    "texto",
    [
        "",
        "curto",
        "         a         ",
        "a" * 20001,
        "a" * 10 + "\x00",
        "a" * 10 + "\r\n",
        "a" * 10 + "\x1b[0m",
        None,
        123,
        ["a" * 10],
    ],
    ids=[
        "vazio",
        "curto",
        "so-espacos",
        "grande",
        "controle-nulo",
        "cr",
        "escape",
        "none",
        "inteiro",
        "lista",
    ],
)
def test_req_8_3_texto_invalido_e_recusado_sem_ecoar_o_conteudo(texto):
    """[005] REQ-8.3: menos de 10 úteis, mais de 20 000, controle (exceto \\n e \\t) ou não-texto; a mensagem não repete o texto."""
    with pytest.raises(ErroValidacao) as erro:
        domain.validar_texto(texto)

    assert "texto" in erro.value.campos
    assert "a" * 10 not in json.dumps(erro.value.campos)


@pytest.mark.parametrize(
    ("visibilidade", "trecho", "tamanho", "ok"),
    [
        ("partial", {"inicio": 0, "fim": 5}, 10, True),
        ("partial", {"inicio": 0, "fim": 10}, 10, True),
        ("partial", {"inicio": 9, "fim": 10}, 10, True),
        ("partial", {"inicio": 5, "fim": 5}, 10, False),
        ("partial", {"inicio": 6, "fim": 5}, 10, False),
        ("partial", {"inicio": -1, "fim": 5}, 10, False),
        ("partial", {"inicio": 0, "fim": 11}, 10, False),
        ("partial", {"inicio": 0, "fim": 10**12}, 10, False),
        ("partial", {"inicio": "0", "fim": 5}, 10, False),
        ("partial", {"inicio": 0.5, "fim": 5}, 10, False),
        ("partial", {"inicio": True, "fim": 5}, 10, False),
        ("partial", {"inicio": None, "fim": 5}, 10, False),
        ("partial", {"inicio": 0}, 10, False),
        ("partial", {}, 10, False),
        ("partial", None, 10, False),
        ("partial", "0-5", 10, False),
        ("full", {"inicio": 0, "fim": 5}, 10, False),
        ("private", {"inicio": 0, "fim": 5}, 10, False),
        ("full", None, 10, True),
        ("private", None, 10, True),
        ("secreto", None, 10, False),
        (None, None, 10, False),
    ],
)
def test_req_8_4_trecho_so_com_partial_e_dentro_do_texto(visibilidade, trecho, tamanho, ok):
    """[005] REQ-8.4 / ABU-11: 0 ≤ inicio < fim ≤ tamanho; só em `partial`; só inteiros de verdade."""
    texto = "x" * tamanho
    if ok:
        domain.validar_visibilidade_e_trecho(visibilidade, trecho, texto)
    else:
        with pytest.raises(ErroValidacao):
            domain.validar_visibilidade_e_trecho(visibilidade, trecho, texto)


def test_req_8_4_o_tamanho_do_trecho_conta_pontos_de_codigo():
    """[005] REQ-8.4: com emoji, o fim máximo é o número de pontos de código."""
    texto = "a😀b😀c1234567"
    assert domain.validar_visibilidade_e_trecho(
        "partial", {"inicio": 0, "fim": len(texto)}, texto
    ) == (0, len(texto))
    with pytest.raises(ErroValidacao):
        domain.validar_visibilidade_e_trecho("partial", {"inicio": 0, "fim": len(texto) + 1}, texto)
