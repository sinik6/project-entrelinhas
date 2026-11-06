"""[005] Lista de registros por mês: fuso de São Paulo, ordem, mês inválido ou futuro, sem grupo, isolamento."""

import pytest

from .conftest import entregar


def _dia(relogio, dia, hora=12, minuto=0, mes=11, ano=2026):
    relogio.fixar(ano, mes, dia, hora, minuto)


def test_req_10_1_lista_os_registros_do_grupo_no_mes_do_mais_novo_para_o_mais_antigo(
    dono, parceiro, relogio
):
    """[005] REQ-10.1: dos dois membros, filtrados pela visibilidade, ordem decrescente."""
    bia = parceiro()
    _dia(relogio, 3)
    a = entregar(dono).json()["id"]
    _dia(relogio, 4)
    b = entregar(bia).json()["id"]
    _dia(relogio, 5)
    c = entregar(dono, visibilidade="private").json()["id"]
    relogio.fixar(2026, 11, 20)

    do_dono = dono.get("/api/v1/registros?mes=2026-11").json()
    da_bia = bia.get("/api/v1/registros?mes=2026-11").json()

    assert [r["id"] for r in do_dono] == [c, b, a]
    assert [r["id"] for r in da_bia] == [c, b, a]
    assert [r["meu"] for r in do_dono] == [True, False, True]
    assert da_bia[0]["visibilidade_efetiva"] == "private"  # o `private` do dono, visto pela Bia
    assert da_bia[2]["texto_visivel"] is not None  # o `full` do dono


def test_req_10_1_o_mes_e_o_de_sao_paulo_e_nao_o_do_utc(dono, relogio):
    """[005] REQ-10.1: 23h30 de 30/11 em São Paulo (02h30 UTC de 01/12) é novembro; 00h30 de 01/12 em SP é dezembro."""
    relogio.fixar(2026, 12, 1, 2, 30)  # 23h30 de 30/11 em São Paulo
    novembro = entregar(dono).json()["id"]
    relogio.fixar(2026, 12, 1, 3, 30)  # 00h30 de 01/12 em São Paulo
    dezembro = entregar(dono).json()["id"]
    relogio.fixar(2026, 12, 15)

    assert [r["id"] for r in dono.get("/api/v1/registros?mes=2026-11").json()] == [novembro]
    assert [r["id"] for r in dono.get("/api/v1/registros?mes=2026-12").json()] == [dezembro]


def test_req_10_1_mes_sem_registros_devolve_lista_vazia(dono, relogio):
    """[005] REQ-10.1."""
    relogio.fixar(2026, 11, 5)

    assert dono.get("/api/v1/registros?mes=2026-10").json() == []


@pytest.mark.parametrize(
    "mes",
    [
        "",
        "2026",
        "2026-13",
        "2026-00",
        "26-11",
        "2026-1",
        "2026/11",
        "abcd-ef",
        "2026-11-01",
        " 2026-11",
        "2026-11 ",
    ],
)
def test_req_10_2_mes_mal_formado_da_422(dono, relogio, mes):
    """[005] REQ-10.2 / NFR-REG-2."""
    relogio.fixar(2026, 11, 5)

    resposta = dono.get("/api/v1/registros", {"mes": mes})

    assert resposta.status_code == 422, mes
    assert "mes" in resposta.json()["campos"]


def test_req_10_2_sem_o_parametro_mes_da_422(dono):
    """[005] REQ-10.2."""
    resposta = dono.get("/api/v1/registros")

    assert resposta.status_code == 422
    assert "mes" in resposta.json()["campos"]


def test_req_10_2_mes_futuro_da_422_e_o_mes_atual_e_aceito(dono, relogio):
    """[005] REQ-10.2: o mês corrente vale; o seguinte não."""
    relogio.fixar(2026, 11, 5)

    assert dono.get("/api/v1/registros?mes=2026-11").status_code == 200
    assert dono.get("/api/v1/registros?mes=2026-12").status_code == 422
    assert dono.get("/api/v1/registros?mes=2099-01").status_code == 422


def test_req_10_3_sem_grupo_a_lista_e_vazia(novo_participante, logar, relogio):
    """[005] REQ-10.3: sem grupo (ou sem perfil) devolve [], não erro."""
    relogio.fixar(2026, 11, 5)
    novo_participante("solo@example.com", nome="Solo")
    novo_participante("adm@example.com", nome=None)

    for email in ("solo@example.com", "adm@example.com"):
        resposta = logar(email).get("/api/v1/registros?mes=2026-11")

        assert resposta.status_code == 200, email
        assert resposta.json() == []


def test_abu_10_a_lista_nunca_traz_registro_de_outro_grupo(dono, estranho, relogio):
    """[005] ABU-10 / CTL-35: o estranho tem a lista do grupo dele (vazia), não a do dono."""
    relogio.fixar(2026, 11, 5)
    entregar(dono)

    assert estranho.get("/api/v1/registros?mes=2026-11").json() == []
