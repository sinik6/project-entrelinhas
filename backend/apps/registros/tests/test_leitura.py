"""[005] Leitura por todas as rotas, como autor e como parceiro: o texto escondido nunca vaza (Art. 12)."""

import json

import pytest

from .conftest import entregar, foto_manuscrito, marcadores

TOKENS = marcadores(8)
TEXTO = "".join(TOKENS)  # 40 pontos de código; cada marcador ocupa 5
ESCONDIDOS = TOKENS[:3] + TOKENS[5:]  # no trecho [15, 25) só os marcadores 3 e 4 aparecem
VISIVEIS = TOKENS[3:5]


def _entregar_partial(dono, texto=TEXTO):
    resposta = entregar(dono, texto=texto, visibilidade="partial", trecho={"inicio": 15, "fim": 25})
    assert resposta.status_code == 201, resposta.content
    return resposta.json()


def _todas_as_respostas_do_parceiro(bia, registro_id) -> list[str]:
    """Tudo o que o parceiro consegue obter sobre o registro, em texto: detalhe, lista, erros e as fotos."""
    saidas = []
    for url in (
        f"/api/v1/registros/{registro_id}",
        "/api/v1/registros?mes=2000-01",
        "/api/v1/registros?mes=lixo",
        "/api/v1/registros?mes=2099-01",
    ):
        saidas.append(bia.get(url).content.decode())
    # a lista do mês de hoje (onde o registro mora)
    from django.utils import timezone

    mes = timezone.localdate().strftime("%Y-%m")
    saidas.append(bia.get(f"/api/v1/registros?mes={mes}").content.decode())
    # erros de escrita do parceiro não podem repetir texto de ninguém
    saidas.append(
        bia.put(
            f"/api/v1/registros/{registro_id}",
            {"texto": "x"},
            format="json",
            HTTP_X_CSRFTOKEN=bia.token(),
        ).content.decode()
    )
    saidas.append(
        bia.delete(
            f"/api/v1/registros/{registro_id}", HTTP_X_CSRFTOKEN=bia.token()
        ).content.decode()
    )
    return saidas


def test_req_9_1_autor_le_o_proprio_registro_inteiro_pelo_detalhe_e_pela_lista(dono):
    """[005] REQ-9.1: texto inteiro, visibilidade, trecho, fotos e hora."""
    registro = _entregar_partial(dono)

    detalhe = dono.get(f"/api/v1/registros/{registro['id']}").json()

    assert detalhe["texto"] == TEXTO
    assert detalhe["visibilidade"] == "partial"
    assert detalhe["trecho"] == {"inicio": 15, "fim": 25}
    assert len(detalhe["fotos"]) == 1
    assert detalhe["entregue_em"]
    assert detalhe["autor"] == {"nome": "Dono", "cor": "#4D7C0F", "foto_url": None}
    from django.utils import timezone

    lista = dono.get(f"/api/v1/registros?mes={timezone.localdate():%Y-%m}").json()
    assert [r["id"] for r in lista] == [registro["id"]]
    assert lista[0]["texto"] == TEXTO


def test_req_9_2_parceiro_le_o_texto_inteiro_e_as_fotos_quando_full(dono, parceiro):
    """[005] REQ-9.2."""
    registro = entregar(dono, texto=TEXTO).json()

    visto = parceiro().get(f"/api/v1/registros/{registro['id']}").json()

    assert visto["meu"] is False
    assert visto["visibilidade_efetiva"] == "full"
    assert visto["texto_visivel"] == TEXTO
    assert visto["fotos"] == registro["fotos"]
    assert visto["autor"]["nome"] == "Dono"


def test_req_9_3_parceiro_so_le_o_trecho_e_nada_mais_em_partial(dono, parceiro):
    """[005] REQ-9.3: só o trecho, sem fotos, sem o texto fora dele e sem os offsets."""
    registro = _entregar_partial(dono)

    corpo = parceiro().get(f"/api/v1/registros/{registro['id']}")

    assert corpo.status_code == 200
    visto = corpo.json()
    assert visto["texto_visivel"] == "".join(VISIVEIS)
    assert visto["visibilidade_efetiva"] == "partial"
    assert visto["fotos"] == []
    for escondido in ESCONDIDOS:
        assert escondido not in corpo.content.decode()
    assert not {"texto", "trecho", "visibilidade", "trecho_inicio", "trecho_fim"} & set(visto)


def test_req_9_4_parceiro_so_ve_a_indicacao_em_private(dono, parceiro):
    """[005] REQ-9.4: aviso, hora, sem texto e sem fotos."""
    registro = entregar(dono, texto=TEXTO, visibilidade="private").json()

    corpo = parceiro().get(f"/api/v1/registros/{registro['id']}")

    visto = corpo.json()
    assert visto["visibilidade_efetiva"] == "private"
    assert visto["texto_visivel"] is None
    assert visto["fotos"] == []
    assert visto["aviso"] == "Enviado, mas mantido privado pelo autor"
    assert visto["entregue_em"]
    for token in TOKENS:
        assert token not in corpo.content.decode()


def test_req_9_5_parceiro_ve_a_foto_do_registro_full_e_recebe_404_em_partial_e_private(
    dono, parceiro, relogio
):
    """[005] REQ-9.5 / CTL-33: a foto mostra o texto inteiro, então só sai quando o registro é full."""
    bia = parceiro()
    fotos = {}
    for dia, (visibilidade, trecho) in enumerate(
        [("full", None), ("partial", {"inicio": 0, "fim": 10}), ("private", None)], start=5
    ):
        relogio.fixar(2026, 11, dia)
        resposta = entregar(dono, texto=TEXTO, visibilidade=visibilidade, trecho=trecho)
        assert resposta.status_code == 201, resposta.content
        fotos[visibilidade] = resposta.json()["fotos"][0]

    assert bia.get(f"/api/v1/fotos/{fotos['full']}/arquivo").status_code == 200
    assert bia.get(f"/api/v1/fotos/{fotos['partial']}/arquivo").status_code == 404
    assert bia.get(f"/api/v1/fotos/{fotos['private']}/arquivo").status_code == 404
    for visibilidade in fotos.values():
        assert (
            dono.get(f"/api/v1/fotos/{visibilidade}/arquivo").status_code == 200
        )  # o autor sempre vê as dele


def test_req_9_6_registro_e_foto_de_outro_grupo_dao_404(dono, estranho):
    """[005] REQ-9.6 / CTL-35: nunca 403."""
    registro = entregar(dono).json()

    assert estranho.get(f"/api/v1/registros/{registro['id']}").status_code == 404
    assert estranho.get(f"/api/v1/fotos/{registro['fotos'][0]}/arquivo").status_code == 404


def test_abu_10_id_inexistente_ou_malformado_da_404(dono):
    """[005] ABU-10."""
    assert dono.get("/api/v1/registros/00000000-0000-4000-8000-000000000000").status_code == 404
    assert dono.get("/api/v1/registros/nao-e-uuid").status_code == 404


def test_req_9_7_nenhum_ponto_do_texto_escondido_vaza_por_nenhuma_rota(dono, parceiro):
    """[005] REQ-9.7 / ABU-8 / Art. 12: corpo, lista, erros e cabeçalhos do parceiro não trazem texto escondido."""
    partial = _entregar_partial(dono)
    bia = parceiro()

    saidas = _todas_as_respostas_do_parceiro(bia, partial["id"])

    for saida in saidas:
        for escondido in ESCONDIDOS:
            assert escondido not in saida
    assert any(VISIVEIS[0] in s for s in saidas), (
        "o trecho visível precisa aparecer (o teste enxerga a resposta certa)"
    )


def test_req_9_7_private_nao_vaza_nem_pelo_tamanho_ou_pela_lista(dono, parceiro, relogio):
    """[005] REQ-9.7 / ABU-8: o parceiro não descobre nem o tamanho do texto privado."""
    relogio.fixar(2026, 11, 5)
    curto = entregar(dono, texto="a" * 10, visibilidade="private").json()
    relogio.fixar(2026, 11, 6)
    longo = entregar(dono, texto="b" * 5000, visibilidade="private").json()
    bia = parceiro()

    a = bia.get(f"/api/v1/registros/{curto['id']}").json()
    b = bia.get(f"/api/v1/registros/{longo['id']}").json()

    for campo in ("id", "data", "entregue_em"):
        a.pop(campo), b.pop(campo)
    a["fotos"], b["fotos"] = [], []
    assert a == b, "dois registros privados de tamanhos muito diferentes têm que parecer iguais"
    assert "bbbb" not in json.dumps(b)


def test_req_9_7_cabecalhos_da_resposta_do_parceiro_nao_carregam_texto(dono, parceiro):
    """[005] REQ-9.7: nenhum cabeçalho com texto, tamanho ou posição."""
    partial = _entregar_partial(dono)

    resposta = parceiro().get(f"/api/v1/registros/{partial['id']}")

    cabecalhos = " ".join(f"{k}: {v}" for k, v in resposta.items())
    for escondido in ESCONDIDOS:
        assert escondido not in cabecalhos


@pytest.mark.parametrize("visibilidade", ["private", "partial"])
def test_req_9_7_o_parceiro_nao_consegue_a_foto_por_a_lista_nem_por_id_conhecido(
    dono, parceiro, visibilidade, relogio
):
    """[005] REQ-9.7: a lista do parceiro de um registro escondido não traz id de foto."""
    relogio.fixar(2026, 11, 5)
    trecho = {"inicio": 0, "fim": 10} if visibilidade == "partial" else None
    registro = entregar(dono, texto=TEXTO, visibilidade=visibilidade, trecho=trecho).json()
    bia = parceiro()

    lista = bia.get("/api/v1/registros?mes=2026-11").json()

    assert [r["id"] for r in lista] == [registro["id"]], (
        "o registro tem que estar na lista (senão o teste não prova nada)"
    )
    assert registro["fotos"][0] not in json.dumps(lista)


def test_req_9_1_foto_do_registro_sai_na_ordem_da_entrega(dono):
    """[005] REQ-9.1: a ordem das fotos é a que o autor mandou."""
    fotos = [foto_manuscrito(dono) for _ in range(3)]
    registro = entregar(dono, fotos=list(reversed(fotos))).json()

    assert dono.get(f"/api/v1/registros/{registro['id']}").json()["fotos"] == list(reversed(fotos))
