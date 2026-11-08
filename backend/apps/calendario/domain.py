"""O estado de cada dia do calendário (spec 009), calculado só dos registros e da data de entrada. Função pura, sem banco."""

import calendar
from datetime import date, datetime

JANELA_JUNTOS_SEGUNDOS = 7200  # duas horas, inclusive


def dias_do_mes(ano: int, mes: int, hoje: date) -> list[date]:
    """Os dias do mês até hoje (um mês passado vem inteiro; um futuro, vazio)."""
    ultimo = calendar.monthrange(ano, mes)[1]
    return [d for d in (date(ano, mes, n) for n in range(1, ultimo + 1)) if d <= hoje]


def estado_do_dia(dia: date, entregou: bool, entrou_em: date | None, hoje: date) -> str:
    """`escreveu` > `fora` > `pendente` (hoje) > `falhou`. Registro existente vale mais que a data de entrada."""
    if entregou:
        return "escreveu"
    if entrou_em is not None and dia < entrou_em:
        return "fora"
    return "pendente" if dia == hoje else "falhou"


def escreveram_juntos(horarios: list[datetime]) -> bool:
    """Os dois entregaram e a diferença entre os horários é de até 2 horas (inclusive). Simétrico."""
    if len(horarios) != 2:
        return False
    return abs((horarios[0] - horarios[1]).total_seconds()) <= JANELA_JUNTOS_SEGUNDOS


def estado_do_mes(
    entregas: dict[tuple[int, date], datetime],
    membros: list[tuple[int, date | None]],
    hoje: date,
    ano: int,
    mes: int,
) -> list[dict]:
    """`entregas[(membro, dia)]` é o instante da entrega; `membros` é `[(id, entrou_em)]` na ordem de exibição.

    O dia de cada entrega já vem calculado (a data do registro, em São Paulo): nada aqui olha o relógio do servidor.
    """
    resultado = []
    for dia in dias_do_mes(ano, mes, hoje):
        horarios = [entregas[(m, dia)] for m, _ in membros if (m, dia) in entregas]
        resultado.append(
            {
                "data": dia,
                "estados": [
                    estado_do_dia(dia, (m, dia) in entregas, entrou, hoje) for m, entrou in membros
                ],
                "juntos": len(membros) == 2 and escreveram_juntos(horarios),
            }
        )
    return resultado
