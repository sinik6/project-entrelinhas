"""Roteiro de mutação do calendário (spec 009). Não é coletado pelo pytest.

Uso, dentro de `backend/`, com o PostgreSQL de teste de pé:  python apps/calendario/tests/mutacao.py
"""

import subprocess
from pathlib import Path

D = Path("apps/calendario/domain.py")
S = Path("apps/calendario/services.py")
A = Path("apps/acesso/services.py")

MUTANTES = [
    ("janela de 7199 s", D, "JANELA_JUNTOS_SEGUNDOS = 7200", "JANELA_JUNTOS_SEGUNDOS = 7199"),
    ("janela de 7201 s", D, "JANELA_JUNTOS_SEGUNDOS = 7200", "JANELA_JUNTOS_SEGUNDOS = 7201"),
    (
        "juntos sem módulo (assimétrico)",
        D,
        "return abs((horarios[0] - horarios[1]).total_seconds()) <= JANELA_JUNTOS_SEGUNDOS",
        "return (horarios[0] - horarios[1]).total_seconds() <= JANELA_JUNTOS_SEGUNDOS",
    ),
    (
        "juntos com um só",
        D,
        "if len(horarios) != 2:\n        return False",
        "if len(horarios) < 1:\n        return False",
    ),
    (
        "registro não vence a data de entrada",
        D,
        '    if entregou:\n        return "escreveu"\n    if entrou_em',
        '    if entrou_em is not None and dia < entrou_em:\n        return "fora"\n    if entregou:\n        return "escreveu"\n    if entrou_em',
    ),
    ("sem estado fora", D, "if entrou_em is not None and dia < entrou_em:", "if False:"),
    ("hoje vira falha", D, 'return "pendente" if dia == hoje else "falhou"', 'return "falhou"'),
    (
        "dia de amanhã aparece",
        D,
        "if d <= hoje]",
        "if d <= hoje.replace(day=min(hoje.day + 1, 28))]",
    ),
    ("mês futuro aceito", S, "if (ano, numero) > (hoje.year, hoje.month):", "if False:"),
    (
        "mês anterior à entrada aceito",
        S,
        "if datas and (ano, numero) < (min(datas).year, min(datas).month):",
        "if False:",
    ),
    (
        "registros de outro grupo",
        S,
        "            grupo_id=grupo_id,\n            autor_id__in",
        "            autor_id__in",
    ),
    (
        "grupo de outro",
        S,
        "Perfil.objects.filter(grupo_id=grupo_id).order_by",
        "Perfil.objects.all().order_by",
    ),
    (
        "dia pelo UTC",
        S,
        "hoje = registros.dia_de(registros.agora())",
        "hoje = registros.agora().date()",
    ),
    (
        "criar grupo não grava a entrada",
        A,
        "        perfil.entrou_em = _hoje_em_sao_paulo()\n",
        "        pass\n",
    ),
    ("convite não grava a entrada", A, "            entrou_em=_hoje_em_sao_paulo(),\n", ""),
]


def main() -> None:
    originais = {p: p.read_text(encoding="utf-8") for p in (D, S, A)}
    vivos = []
    try:
        for nome, arquivo, antigo, novo in MUTANTES:
            texto = originais[arquivo]
            assert antigo in texto, f"trecho não encontrado: {nome}"
            arquivo.write_text(texto.replace(antigo, novo, 1), encoding="utf-8")
            r = subprocess.run(
                [
                    "uv",
                    "run",
                    "pytest",
                    "apps/calendario",
                    "apps/acesso",
                    "-q",
                    "-x",
                    "--no-header",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            morto = r.returncode != 0
            print(("MORTO " if morto else "VIVO  ") + nome, flush=True)
            if not morto:
                vivos.append(nome)
            arquivo.write_text(texto, encoding="utf-8")
    finally:
        for p, t in originais.items():
            p.write_text(t, encoding="utf-8")
    print("vivos:", vivos)


if __name__ == "__main__":
    main()
