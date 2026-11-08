"""[009] A função pura `estado_do_mes`: escreveu, falhou, pendente, fora, juntos, oráculo e simetria (sem banco)."""

import random
from datetime import UTC, date, datetime, timedelta

import pytest

from apps.calendario import domain

UTC = UTC
HOJE = date(2026, 11, 10)


def entrega(dia: int, hora=12, minuto=0, segundo=0, mes=11):
    return datetime(2026, mes, dia, hora, minuto, segundo, tzinfo=UTC)


def estados(entregas, membros, hoje=HOJE, mes=11):
    return domain.estado_do_mes(entregas, membros, hoje, 2026, mes)


def dia(resultado, n):
    return next(d for d in resultado if d["data"] == date(2026, 11, n))


A, B = 1, 2
AMBOS = [(A, date(2026, 11, 1)), (B, date(2026, 11, 1))]


def test_req_16_1_so_aparecem_os_dias_do_mes_ate_hoje():
    """[009] REQ-16.1."""
    r = estados({}, AMBOS)

    assert [d["data"].day for d in r] == list(range(1, 11))


def test_req_16_1_mes_passado_aparece_inteiro_e_mes_cheio_tem_todos_os_dias():
    """[009] REQ-16.1."""
    assert len(estados({}, [(A, date(2026, 1, 1))], mes=10)) == 31
    assert len(estados({}, [(A, date(2026, 1, 1))], hoje=date(2026, 12, 5), mes=11)) == 30


def test_req_16_2_escreveu_com_registro_no_dia():
    """[009] REQ-16.2."""
    r = estados({(A, date(2026, 11, 3)): entrega(3)}, AMBOS)

    assert dia(r, 3)["estados"] == ["escreveu", "falhou"]


def test_req_16_3_falhou_no_dia_que_terminou_sem_registro_e_pendente_hoje():
    """[009] REQ-16.3."""
    r = estados({}, AMBOS)

    assert dia(r, 4)["estados"] == ["falhou", "falhou"]
    assert dia(r, 10)["estados"] == ["pendente", "pendente"]


def test_req_16_3_hoje_com_registro_e_escreveu_e_o_outro_pendente():
    """[009] REQ-16.3."""
    r = estados({(A, HOJE): entrega(10)}, AMBOS)

    assert dia(r, 10)["estados"] == ["escreveu", "pendente"]


def test_req_16_3_fora_antes_de_entrar_no_grupo():
    """[009] REQ-16.3: dia anterior à entrada não conta como falha."""
    membros = [(A, date(2026, 11, 1)), (B, date(2026, 11, 6))]

    r = estados({}, membros)

    assert dia(r, 5)["estados"] == ["falhou", "fora"]
    assert dia(r, 6)["estados"] == ["falhou", "falhou"]


def test_req_16_3_registro_antes_da_entrada_vale_escreveu_nao_fora():
    """[009] REQ-16.2/16.3: se há registro, o dia é `escreveu`, mesmo que a data de entrada seja posterior."""
    membros = [(A, date(2026, 11, 8)), (B, date(2026, 11, 1))]

    r = estados({(A, date(2026, 11, 5)): entrega(5)}, membros)

    assert dia(r, 5)["estados"] == ["escreveu", "falhou"]


def test_req_16_3_sem_data_de_entrada_nunca_e_fora():
    """[009] REQ-16.3: `entrou_em` desconhecido não esconde falha nem apaga dia."""
    r = estados({}, [(A, None), (B, date(2026, 11, 1))])

    assert dia(r, 1)["estados"] == ["falhou", "falhou"]


@pytest.mark.parametrize(
    "segundos,juntos",
    [(0, True), (3600, True), (7199, True), (7200, True), (7201, False), (20_000, False)],
)
def test_req_16_4_16_5_juntos_ate_duas_horas_inclusive(segundos, juntos):
    """[009] REQ-16.4 / REQ-16.5: 7199 e 7200 s juntos; 7201 s não."""
    base = entrega(3, 8, 0, 0)
    r = estados(
        {(A, date(2026, 11, 3)): base, (B, date(2026, 11, 3)): base + timedelta(seconds=segundos)},
        AMBOS,
    )

    assert dia(r, 3)["juntos"] is juntos
    assert dia(r, 3)["estados"] == ["escreveu", "escreveu"]


def test_req_16_5_so_um_escreveu_nao_e_juntos():
    """[009] REQ-16.5 / PROP-12."""
    r = estados({(A, date(2026, 11, 3)): entrega(3)}, AMBOS)

    assert dia(r, 3)["juntos"] is False


def test_req_16_5_dias_diferentes_nao_formam_juntos_mesmo_perto_da_meia_noite():
    """[009] REQ-16.5: 23h50 de um dia e 00h10 do outro: são dias diferentes (a data vem do registro)."""
    r = estados(
        {
            (A, date(2026, 11, 3)): entrega(3, 23, 50),
            (B, date(2026, 11, 4)): entrega(4, 0, 10),
        },
        AMBOS,
    )

    assert dia(r, 3)["juntos"] is False and dia(r, 4)["juntos"] is False


def test_prop_12_juntos_e_simetrico():
    """[009] PROP-12: trocar quem entregou primeiro não muda nada."""
    a, b = entrega(3, 8), entrega(3, 9, 30)

    um = estados({(A, date(2026, 11, 3)): a, (B, date(2026, 11, 3)): b}, AMBOS)
    outro = estados({(A, date(2026, 11, 3)): b, (B, date(2026, 11, 3)): a}, AMBOS)

    assert dia(um, 3)["juntos"] == dia(outro, 3)["juntos"] is True


def oraculo(entregas, membros, hoje, mes):
    """Definição direta das regras, escrita de outro jeito: um dia de cada vez, um membro de cada vez."""
    saida = {}
    n = 1
    while True:
        try:
            d = date(2026, mes, n)
        except ValueError:
            break
        n += 1
        if d > hoje:
            continue
        estado = []
        for membro, entrou in membros:
            if (membro, d) in entregas:
                estado.append("escreveu")
            elif entrou is not None and d < entrou:
                estado.append("fora")
            elif d == hoje:
                estado.append("pendente")
            else:
                estado.append("falhou")
        juntos = (
            len(membros) == 2
            and all((m, d) in entregas for m, _ in membros)
            and abs((entregas[(A, d)] - entregas[(B, d)]).total_seconds()) <= 7200
        )
        saida[d] = (estado, juntos)
    return saida


def test_prop_11_12_o_resultado_bate_com_o_oraculo_em_1000_casos_sorteados():
    """[009] PROP-11 / PROP-12: entregas sorteadas, inclusive nas bordas de 2 horas e perto da meia-noite."""
    r = random.Random(2026_11)
    bordas = [0, 1, 7199, 7200, 7201, 3600, 43_200]
    for _ in range(1000):
        hoje = date(2026, 11, r.randrange(1, 31))
        entradas = [
            date(2026, 11, r.randrange(1, 31)) if r.random() < 0.7 else None for _ in range(2)
        ]
        membros = [(A, entradas[0]), (B, entradas[1])]
        entregas = {}
        for n in range(1, 31):
            d = date(2026, 11, n)
            if r.random() < 0.55:
                base = datetime(2026, 11, n, r.choice([0, 8, 23]), r.randrange(60), tzinfo=UTC)
                entregas[(A, d)] = base
                if r.random() < 0.7:
                    entregas[(B, d)] = base + timedelta(
                        seconds=r.choice(bordas) * r.choice([1, -1])
                    )
        esperado = oraculo(entregas, membros, hoje, 11)

        obtido = domain.estado_do_mes(entregas, membros, hoje, 2026, 11)

        assert {x["data"]: (x["estados"], x["juntos"]) for x in obtido} == esperado, (
            hoje,
            entradas,
        )
