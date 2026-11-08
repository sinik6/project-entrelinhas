"""[009] A rota `GET /calendario`: forma, resposta mínima, mês inválido, sem grupo, outro grupo, virada do dia, consultas."""

import json
from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.acesso.models import Perfil

from .conftest import calendario, entregar_em


def dia(resposta, n, mes="2026-11"):
    return next(d for d in resposta.json()["dias"] if d["data"] == f"{mes}-{n:02d}")


@pytest.fixture
def desde_o_dia_1(par):
    """Os dois entraram no grupo em 1º de novembro."""
    Perfil.objects.update(entrou_em=date(2026, 11, 1))
    return par


def test_req_16_1_forma_da_resposta_membros_e_dias_alinhados(desde_o_dia_1, relogio):
    """[009] REQ-16.1 / CTL-61: `membros` e `estados` alinhados; só os dias até hoje."""
    dono, _ = desde_o_dia_1
    relogio.fixar(2026, 11, 5)

    resposta = calendario(dono, "2026-11")

    assert resposta.status_code == 200, resposta.content
    corpo = resposta.json()
    assert corpo["mes"] == "2026-11" and corpo["hoje"] == "2026-11-05"
    assert [m["nome"] for m in corpo["membros"]] == ["Dono", "Bia"]
    assert corpo["membros"][1]["cor"] == "#B45309"
    assert [d["data"] for d in corpo["dias"]] == [f"2026-11-0{n}" for n in range(1, 6)]
    assert all(len(d["estados"]) == 2 for d in corpo["dias"])


def test_req_16_2_a_16_5_estados_pela_rota(desde_o_dia_1, relogio):
    """[009] REQ-16.2 a 16.5: escreveu, falhou, pendente e juntos."""
    dono, parceiro = desde_o_dia_1
    entregar_em(relogio, dono, 2026, 11, 2, 12, 0)
    entregar_em(relogio, parceiro, 2026, 11, 2, 13, 59)  # 1h59 depois: juntos
    entregar_em(relogio, dono, 2026, 11, 3, 12, 0)
    entregar_em(relogio, parceiro, 2026, 11, 3, 14, 1)  # 2h01 depois: não
    relogio.fixar(2026, 11, 5, 12)

    r = calendario(dono, "2026-11")

    assert dia(r, 1) == {"data": "2026-11-01", "estados": ["falhou", "falhou"], "juntos": False}
    assert dia(r, 2)["estados"] == ["escreveu", "escreveu"] and dia(r, 2)["juntos"] is True
    assert dia(r, 3)["estados"] == ["escreveu", "escreveu"] and dia(r, 3)["juntos"] is False
    assert dia(r, 4)["estados"] == ["falhou", "falhou"]
    assert dia(r, 5)["estados"] == ["pendente", "pendente"]


def test_req_16_2_registro_privado_conta_como_escreveu_para_o_parceiro(desde_o_dia_1, relogio):
    """[009] REQ-16.2 (suposição): `private` conta; o parceiro só vê que houve entrega."""
    dono, parceiro = desde_o_dia_1
    entregar_em(relogio, dono, 2026, 11, 2, visibilidade="private", texto="TEXTO-PRIVADO-DO-DONO")
    relogio.fixar(2026, 11, 3)

    r = calendario(parceiro, "2026-11")

    assert dia(r, 2)["estados"] == ["escreveu", "falhou"]
    assert "PRIVADO" not in r.content.decode()


def test_req_16_3_fora_antes_da_entrada_vem_da_data_do_perfil(par, relogio):
    """[009] REQ-16.3."""
    dono, _ = par
    Perfil.objects.filter(nome="Dono").update(entrou_em=date(2026, 11, 1))
    Perfil.objects.filter(nome="Bia").update(entrou_em=date(2026, 11, 3))
    relogio.fixar(2026, 11, 5)

    r = calendario(dono, "2026-11")

    assert dia(r, 2)["estados"] == ["falhou", "fora"]
    assert dia(r, 3)["estados"] == ["falhou", "falhou"]


def test_req_16_6_sem_horarios_texto_visibilidade_nem_email(desde_o_dia_1, relogio):
    """[009] REQ-16.6 / CTL-61: a resposta é mínima."""
    dono, parceiro = desde_o_dia_1
    entregar_em(relogio, dono, 2026, 11, 2, 12, 34, 56, texto="TEXTO-SECRETO-DO-REGISTRO")
    entregar_em(relogio, parceiro, 2026, 11, 2, 13, 0, visibilidade="private")
    relogio.fixar(2026, 11, 3)

    r = calendario(parceiro, "2026-11")
    corpo = r.content.decode()

    for proibido in (
        "12:34",
        "13:00",
        "T12",
        "SECRETO",
        "texto",
        "visibilidade",
        "email",
        "@",
        "entregue",
        "partial",
        "full",
    ):
        assert proibido not in corpo, proibido
    assert set(json.loads(corpo)) == {"mes", "hoje", "membros", "dias"}
    assert all(set(d) == {"data", "estados", "juntos"} for d in r.json()["dias"])
    assert all(set(m) <= {"nome", "cor", "foto_url"} for m in r.json()["membros"])


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
    ],
)
def test_req_16_7_mes_mal_formado_da_422(desde_o_dia_1, relogio, mes):
    """[009] REQ-16.7 / NFR-CAL-2."""
    relogio.fixar(2026, 11, 5)

    resposta = calendario(desde_o_dia_1[0], mes)

    assert resposta.status_code == 422
    assert "mes" in resposta.json()["campos"]


def test_req_16_7_mes_futuro_e_mes_anterior_a_entrada_do_grupo_dao_422(desde_o_dia_1, relogio):
    """[009] REQ-16.7."""
    dono, _ = desde_o_dia_1
    relogio.fixar(2026, 11, 5)

    assert calendario(dono, "2026-12").status_code == 422
    assert calendario(dono, "2026-10").status_code == 422
    assert calendario(dono, "2026-11").status_code == 200


def test_req_16_8_sem_grupo_devolve_calendario_vazio(novo_participante, logar, relogio):
    """[009] REQ-16.8."""
    novo_participante("solo@example.com", nome="Solo")
    solo = logar("solo@example.com")
    relogio.fixar(2026, 11, 5)

    resposta = calendario(solo, "2026-11")

    assert resposta.status_code == 200
    assert resposta.json() == {"mes": "2026-11", "hoje": "2026-11-05", "membros": [], "dias": []}


def test_req_16_8_conta_sem_perfil_tambem_recebe_vazio(novo_participante, logar, relogio):
    """[009] REQ-16.8."""
    novo_participante("adm@example.com", nome=None)
    relogio.fixar(2026, 11, 5)

    assert calendario(logar("adm@example.com"), "2026-11").json()["membros"] == []


def test_req_16_1_sem_sessao_da_401(cliente):
    """[009] REQ-16.1."""
    assert calendario(cliente, "2026-11").status_code in (401, 403)


def test_abu_19_so_devolve_o_calendario_do_proprio_grupo(desde_o_dia_1, estranho, relogio):
    """[009] ABU-19: quem é de outro grupo não vê os membros nem os dias do primeiro."""
    dono, _ = desde_o_dia_1
    entregar_em(relogio, dono, 2026, 11, 2)
    Perfil.objects.filter(nome="Caio").update(entrou_em=date(2026, 11, 1))
    relogio.fixar(2026, 11, 5)

    r = calendario(estranho, "2026-11")

    assert r.status_code == 200
    assert [m["nome"] for m in r.json()["membros"]] == ["Caio"]
    assert dia(r, 2)["estados"] == ["falhou"]


@pytest.mark.parametrize(
    "hora,minuto,segundo,esperado",
    [
        (2, 59, 59, "2026-11-04"),  # 23:59:59 de 04/11 em São Paulo
        (3, 0, 0, "2026-11-05"),  # 00:00:00 de 05/11 em São Paulo
        (3, 0, 1, "2026-11-05"),
    ],
)
def test_abu_20_req_16_9_a_virada_do_dia_e_a_de_sao_paulo(
    desde_o_dia_1, relogio, hora, minuto, segundo, esperado
):
    """[009] ABU-20 / REQ-16.9: o instante UTC cai no dia de São Paulo certo."""
    dono, _ = desde_o_dia_1
    entregar_em(relogio, dono, 2026, 11, 5, hora, minuto, segundo)
    relogio.fixar(2026, 11, 8, 12)

    r = calendario(dono, "2026-11")

    escreveu = [d["data"] for d in r.json()["dias"] if d["estados"][0] == "escreveu"]
    assert escreveu == [esperado]


def test_abu_20_juntos_perto_da_meia_noite_so_no_mesmo_dia_de_sao_paulo(desde_o_dia_1, relogio):
    """[009] ABU-20: 23h50 e 00h10 de São Paulo são dias diferentes; 22h00 e 23h50 do mesmo dia, juntos? (1h50: sim)."""
    dono, parceiro = desde_o_dia_1
    entregar_em(relogio, dono, 2026, 11, 3, 2, 50)  # 23h50 de 02/11 em SP
    entregar_em(relogio, parceiro, 2026, 11, 3, 3, 10)  # 00h10 de 03/11 em SP
    entregar_em(relogio, dono, 2026, 11, 5, 1, 0)  # 22h00 de 04/11 em SP
    entregar_em(relogio, parceiro, 2026, 11, 5, 2, 50)  # 23h50 de 04/11 em SP
    relogio.fixar(2026, 11, 8, 12)

    r = calendario(dono, "2026-11")

    assert dia(r, 2)["juntos"] is False and dia(r, 3)["juntos"] is False
    assert dia(r, 4)["juntos"] is True


def test_nfr_cal_3_no_maximo_3_consultas_alem_da_autenticacao(desde_o_dia_1, relogio):
    """[009] NFR-CAL-3: independente do mês (31 dias cheios de registros)."""
    dono, parceiro = desde_o_dia_1
    for n in range(1, 11):
        entregar_em(relogio, dono, 2026, 11, n)
        entregar_em(relogio, parceiro, 2026, 11, n, 13)
    relogio.fixar(2026, 11, 28)
    calendario(dono, "2026-11")  # esquenta caches

    with CaptureQueriesContext(connection) as q:
        resposta = calendario(dono, "2026-11")

    assert resposta.status_code == 200
    da_rota = [
        c["sql"]
        for c in q.captured_queries
        if "django_session" not in c["sql"]
        and "auth_user" not in c["sql"]
        and "SAVEPOINT" not in c["sql"]
    ]
    assert len(da_rota) <= 3, da_rota


def test_req_16_9_hoje_e_o_dia_de_sao_paulo_e_nao_o_do_utc(desde_o_dia_1, relogio):
    """[009] REQ-16.9 / ABU-20: 02h30 UTC de 05/11 ainda é 23h30 de 04/11 em São Paulo."""
    dono, _ = desde_o_dia_1
    relogio.fixar(2026, 11, 5, 2, 30)

    r = calendario(dono, "2026-11")

    assert r.json()["hoje"] == "2026-11-04"
    assert dia(r, 4)["estados"] == ["pendente", "pendente"]
    assert [d["data"] for d in r.json()["dias"]][-1] == "2026-11-04"


def test_abu_19_registro_de_outro_grupo_de_um_membro_nao_conta_neste_calendario(
    desde_o_dia_1, estranho, relogio
):
    """[009] ABU-19: a regra de isolamento da 005 vale aqui (o registro fica no grupo de origem)."""
    from django.contrib.auth import get_user_model

    from apps.acesso.models import Grupo
    from apps.registros.models import Registro

    dono, _ = desde_o_dia_1
    bia = get_user_model().objects.get(email="par@example.com")
    antigo = Grupo.objects.create()
    Registro.objects.create(
        grupo=antigo,
        autor=bia,
        data=date(2026, 11, 2),
        texto="registro do grupo antigo",
        visibilidade="full",
        entregue_em="2026-11-02T12:00:00Z",
    )
    relogio.fixar(2026, 11, 5)

    r = calendario(dono, "2026-11")

    assert dia(r, 2)["estados"] == ["falhou", "falhou"]
