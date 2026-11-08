"""Roteiro de mutação do front do calendário (spec 009). Não faz parte do app nem do pytest.

Uso, na raiz do repositório, com o Docker de pé e a imagem `entrelinhas-flutter-sdk:local` construída:
    python frontend/tool/mutacao_calendario.py
Cada mutante troca um trecho do código por uma versão errada e roda `flutter test` inteiro no contêiner: a suíte precisa
FALHAR ("MORTO"). Os originais são restaurados no fim, mesmo com erro.
"""

import os
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FRONT = RAIZ / "frontend"
PAGINA = FRONT / "lib/features/calendario/calendario_page.dart"
MARCADOR = FRONT / "lib/features/calendario/marcador.dart"

MUTANTES = [
    ("escreveu desenhado como falha", MARCADOR, "EstadoDoDia.escreveu => FormaDoMarcador.cheio", "EstadoDoDia.escreveu => FormaDoMarcador.vazadoComX"),
    ("pendente igual a falha", MARCADOR, "EstadoDoDia.pendente => FormaDoMarcador.tracejado", "EstadoDoDia.pendente => FormaDoMarcador.vazadoComX"),
    ("rótulo sem 'não'", PAGINA, "EstadoDoDia.falhou => '${membros[i].nome} não escreveu'", "EstadoDoDia.falhou => '${membros[i].nome} escreveu'"),
    ("rótulo sem 'juntos'", PAGINA, "if (dia.juntos) 'escreveram juntos',", ""),
    ("primeira coluna errada (segunda-feira)", PAGINA, "DateTime(_ano, _mes, 1).weekday % 7", "DateTime(_ano, _mes, 1).weekday - 1"),
    ("selo juntos sempre", PAGINA, "if (dia.juntos)\n                    Padding", "if (true)\n                    Padding"),
    ("passa do mês atual", PAGINA, "onPressed: _noMesAtual || _carregando ? null : _seguinte,", "onPressed: _carregando ? null : _seguinte,"),
    ("mês anterior à entrada sem trava", PAGINA, "onPressed: _semAnterior || _carregando ? null : _anterior,", "onPressed: _carregando ? null : _anterior,"),
    ("lista do dia mostra o mês todo", PAGINA, "if (r.data == widget.dia.chave) r,", "r,"),
    ("fora desenhado como marcador", MARCADOR, "_ => FormaDoMarcador.nenhuma,", "_ => FormaDoMarcador.cheio,"),
]


def main() -> None:
    arquivos = {p: p.read_text(encoding="utf-8") for p in (PAGINA, MARCADOR)}
    vivos = []
    env = {**os.environ, "MSYS_NO_PATHCONV": "1"}
    try:
        for nome, arquivo, antigo, novo in MUTANTES:
            original = arquivos[arquivo]
            if antigo not in original:
                print(f"TRECHO NÃO ENCONTRADO: {nome}", flush=True)
                vivos.append(nome + " (trecho não encontrado)")
                continue
            arquivo.write_text(original.replace(antigo, novo, 1), encoding="utf-8")
            r = subprocess.run(
                [
                    "docker", "run", "--rm", "--user", "root",
                    "-v", f"{FRONT}:/app", "entrelinhas-flutter-sdk:local",
                    "bash", "-c", "cd /app && flutter test --reporter failures-only >/dev/null 2>&1",
                ],
                env=env,
            )
            morto = r.returncode != 0
            print(("MORTO " if morto else "VIVO  ") + nome, flush=True)
            if not morto:
                vivos.append(nome)
            arquivo.write_text(original, encoding="utf-8")
    finally:
        for p, t in arquivos.items():
            p.write_text(t, encoding="utf-8")
    print("vivos:", vivos)


if __name__ == "__main__":
    main()
