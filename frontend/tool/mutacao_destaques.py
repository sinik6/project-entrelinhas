"""Roteiro de mutação do front dos destaques (spec 008, T-3.3). Não faz parte do app nem do pytest.

Uso, na raiz do repositório, com o Docker de pé e a imagem `entrelinhas-flutter-sdk:local` construída:
    python frontend/tool/mutacao_destaques.py
Cada mutante troca um trecho do código por uma versão errada e roda `flutter test` inteiro no contêiner: a suíte precisa
FALHAR ("MORTO"). Os originais são restaurados no fim, mesmo com erro.
"""

import os
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FRONT = RAIZ / "frontend"
PINTURA = FRONT / "lib/features/destaques/pintura.dart"
LEITOR = FRONT / "lib/features/destaques/leitor_page.dart"
FOLHA = FRONT / "lib/features/destaques/folha_de_comentarios.dart"

MUTANTES = [
    (
        "o mais longo fica por cima",
        PINTURA,
        "final cobrindo = faixas.where((f) => f.inicio <= a && b <= f.fim).toList()\n      ..sort(_porTamanho);",
        "final cobrindo = faixas.where((f) => f.inicio <= a && b <= f.fim).toList()\n      ..sort((x, y) => _porTamanho(y, x));",
    ),
    (
        "o toque abre o mais longo",
        PINTURA,
        "      ).where((f) => f.inicio <= offset && offset < f.fim).toList()\n        ..sort(_porTamanho);",
        "      ).where((f) => f.inicio <= offset && offset < f.fim).toList()\n        ..sort((x, y) => _porTamanho(y, x));",
    ),
    ("fundo opaco demais", PINTURA, "const alfaDoDestaque = 0.22;", "const alfaDoDestaque = 0.8;"),
    (
        "o autor em partial perde o deslocamento",
        PINTURA,
        "final base = pontosParaUtf16(texto, trecho.inicio);",
        "const base = 0;",
    ),
    (
        "destaque enviado em UTF-16",
        LEITOR,
        "inicio: trecho.inicioPontos,\n            fim: trecho.fimPontos,",
        "inicio: trecho.inicioUtf16,\n            fim: trecho.fimUtf16,",
    ),
    (
        "sem trava de pedido repetido ao destacar",
        LEITOR,
        "if (trecho == null || _ocupado) return;",
        "if (trecho == null) return;",
    ),
    (
        "sem trava de pedido repetido na folha",
        FOLHA,
        "  Future<void> _executar(Future<void> Function() acao) async {\n    if (_ocupado) return;",
        "  Future<void> _executar(Future<void> Function() acao) async {",
    ),
    (
        "apagar destaque sem confirmação",
        FOLHA,
        "if (ok != true || !mounted) return;",
        "if (!mounted) return;",
    ),
    ("todos veem Apagar destaque", FOLHA, "if (_atual.meu)\n", "if (true)\n"),
    ("todos editam o comentário alheio", FOLHA, "if (c.meu) ...[", "if (true) ...["),
    # Mutante equivalente descartado: afrouxar o `clamp` da seleção no leitor não muda nada, porque `trechoDaSelecao`
    # já corta ao tamanho do texto.
]


def main() -> None:
    arquivos = {p: p.read_text(encoding="utf-8") for p in (PINTURA, LEITOR, FOLHA)}
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
