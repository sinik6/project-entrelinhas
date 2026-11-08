"""[007] Criar destaque: posição contra o texto visível, sem texto visível, sonda do parceiro, PROP-9."""

import json
import random

import pytest

from apps.destaques.models import Destaque

from .conftest import TEXTO, destacar, listar, marcadores, registro_de


def test_req_13_1_membro_destaca_o_texto_visivel_e_recebe_o_trecho(par):
    """[007] REQ-13.1: 201, com o trecho calculado do texto visível."""
    dono, parceiro = par
    registro = registro_de(dono)

    resposta = destacar(parceiro, registro, 0, 7)

    assert resposta.status_code == 201, resposta.content
    d = resposta.json()
    assert d["trecho"] == TEXTO[0:7]
    assert (d["inicio"], d["fim"]) == (0, 7)
    assert d["autor"] == {"nome": "Bia", "cor": "#B45309"}
    assert d["meu"] is True
    assert d["comentarios"] == []
    assert Destaque.objects.count() == 1


def test_req_13_1_o_autor_tambem_destaca_o_proprio_texto(par):
    """[007] REQ-13.1 (suposição): qualquer membro que enxergue o texto, inclusive o autor."""
    dono, _ = par
    registro = registro_de(dono)

    resposta = destacar(dono, registro, 8, 14)

    assert resposta.status_code == 201
    assert resposta.json()["trecho"] == TEXTO[8:14]


def test_req_13_1_em_partial_a_posicao_e_relativa_ao_trecho_visivel(par):
    """[007] REQ-13.1 / ADR-0009: em `partial` o texto visível é só o trecho, para todos."""
    dono, parceiro = par
    registro = registro_de(
        dono,
        texto="ESCONDIDO visivel aqui ESCONDIDO",
        visibilidade="partial",
        trecho={"inicio": 10, "fim": 22},
    )

    do_parceiro = destacar(parceiro, registro, 0, 7)
    do_autor = destacar(dono, registro, 8, 12)

    assert do_parceiro.status_code == 201
    assert do_parceiro.json()["trecho"] == "visivel"
    assert do_autor.json()["trecho"] == "aqui"


@pytest.mark.parametrize(
    "inicio,fim",
    [
        (-1, 5),
        (5, 5),
        (6, 5),
        (0, 10**9),
        (0, 10_000),
        ("1", 5),
        (1.5, 5),
        (True, 5),
        (None, 5),
        (0, None),
        ([0], 5),
        ({"a": 1}, 5),
    ],
)
def test_req_13_2_posicoes_invalidas_dao_422_e_nunca_500(par, inicio, fim):
    """[007] REQ-13.2: inteiros estritos, 0 <= inicio < fim <= tamanho do visível."""
    dono, parceiro = par
    registro = registro_de(dono)

    resposta = destacar(parceiro, registro, inicio, fim)

    assert resposta.status_code == 422, (inicio, fim)
    assert Destaque.objects.count() == 0


def test_req_13_2_campos_faltando_dao_422(par):
    """[007] REQ-13.2."""
    dono, parceiro = par
    registro = registro_de(dono)

    for corpo in ({}, {"inicio": 1}, {"fim": 5}, []):
        assert parceiro.postar(f"/api/v1/registros/{registro}/destaques", corpo).status_code == 422


def test_req_13_3_registro_private_recusa_criar_e_listar_com_409(par):
    """[007] REQ-13.3: para o parceiro e também para o autor."""
    dono, parceiro = par
    registro = registro_de(dono, visibilidade="private")

    for quem in (dono, parceiro):
        assert destacar(quem, registro, 0, 5).status_code == 409
        resposta = listar(quem, registro)
        assert resposta.status_code == 409
        assert resposta.json() == {"detalhe": "Este registro não tem texto para destacar."}
    assert Destaque.objects.count() == 0


def test_req_13_4_destaque_com_comentario_guarda_o_comentario_junto(par):
    """[007] REQ-13.4."""
    dono, parceiro = par
    registro = registro_de(dono)

    resposta = destacar(parceiro, registro, 0, 7, comentario="Gostei muito disso.")

    assert resposta.status_code == 201
    comentarios = resposta.json()["comentarios"]
    assert [c["texto"] for c in comentarios] == ["Gostei muito disso."]
    assert comentarios[0]["meu"] is True
    assert comentarios[0]["autor"]["nome"] == "Bia"


def test_req_13_4_comentario_invalido_nao_deixa_destaque_orfao(par):
    """[007] REQ-13.4 / REQ-14.1: tudo ou nada."""
    dono, parceiro = par
    registro = registro_de(dono)

    resposta = destacar(parceiro, registro, 0, 7, comentario="   ")

    assert resposta.status_code == 422
    assert Destaque.objects.count() == 0


def test_abu_14_sonda_do_parceiro_em_partial_nao_revela_o_escondido_nem_o_tamanho(par):
    """[007] ABU-14 / Art. 12: posições além do trecho, mensagens e listas não trazem o escondido."""
    dono, parceiro = par
    escondido = "SEGREDO-QUE-NAO-PODE-VAZAR-NUNCA"
    texto = f"{escondido} visivel {escondido}"
    ini = len(escondido) + 1
    registro = registro_de(
        dono, texto=texto, visibilidade="partial", trecho={"inicio": ini, "fim": ini + 7}
    )

    tentativas = [(0, 8), (0, len(texto)), (0, len(texto) + 1), (ini, ini + 8), (7, 100), (8, 9)]
    respostas = [destacar(parceiro, registro, a, b) for a, b in tentativas]
    lista = listar(parceiro, registro)

    for r in respostas:
        assert r.status_code == 422, r.content
        corpo = r.content.decode()
        assert "SEGREDO" not in corpo
        assert str(len(texto)) not in corpo, "o tamanho do texto inteiro não pode aparecer"
    assert "SEGREDO" not in lista.content.decode()
    # a mensagem só pode citar o tamanho do VISÍVEL (7), igual para qualquer posição errada
    assert len({r.content for r in respostas}) == 1
    assert "entre 0 e 7," in respostas[0].content.decode()


def test_abu_14_em_full_a_mensagem_cita_so_o_tamanho_do_texto_visivel(par):
    """[007] ABU-14: em `full` o visível é o texto todo."""
    dono, parceiro = par
    registro = registro_de(dono)

    resposta = destacar(parceiro, registro, 0, 10_000)

    assert resposta.status_code == 422
    assert f"entre 0 e {len(TEXTO)}," in resposta.content.decode()


def test_prop_9_trecho_destacado_e_exatamente_o_texto_visivel_fatiado(par, relogio):
    """[007] PROP-9: casos sorteados (semente fixa); nenhum marcador escondido aparece no JSON."""
    dono, parceiro = par
    r = random.Random(2026)
    for rodada in range(6):
        relogio.fixar(2026, 11, 1 + rodada)
        ms = marcadores(12)
        texto = "".join(ms)
        if rodada % 2 == 0:
            visibilidade, trecho, visivel = "full", None, texto
        else:
            a = r.randrange(0, 8) * 5
            visibilidade = "partial"
            trecho = {"inicio": a, "fim": a + r.randrange(1, 4) * 5}
            visivel = texto[trecho["inicio"] : trecho["fim"]]
        registro = registro_de(dono, texto=texto, visibilidade=visibilidade, trecho=trecho)
        for _ in range(25):
            a = r.randrange(0, len(visivel))
            b = r.randrange(a + 1, len(visivel) + 1)
            resposta = destacar(parceiro, registro, a, b)
            assert resposta.status_code == 201
            assert resposta.json()["trecho"] == visivel[a:b]
        corpo = json.dumps(listar(parceiro, registro).json())
        escondidos = [m for m in ms if m not in visivel]
        assert not any(m in corpo for m in escondidos), (visibilidade, trecho)
