"""Roteiro de mutação do front dos registros (spec 006, T-3.3). Não faz parte do app nem do pytest.

Uso, na raiz do repositório, com o Docker de pé e a imagem `entrelinhas-flutter-sdk:local` construída:
    python frontend/tool/mutacao_registros.py
Cada mutante troca um trecho do código por uma versão errada e roda `flutter test` inteiro no contêiner: a suíte precisa
FALHAR (mutante "MORTO"). Os arquivos originais são restaurados no fim, mesmo com erro. "VIVO" = regra sem teste.
"""

import os
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FRONT = RAIZ / "frontend"
TEXTO = FRONT / "lib/shared/texto.dart"
HOJE = FRONT / "lib/features/hoje/hoje_page.dart"
CARTAO = FRONT / "lib/features/diario/cartao_de_registro.dart"
DIARIO = FRONT / "lib/features/diario/diario_page.dart"

MUTANTES = [
    (
        "início da seleção cresce para fora do grafema",
        TEXTO,
        "if (inicio < 0 && posicao >= baixo) inicio = posicao;",
        "if (posicao <= baixo) inicio = posicao;",
    ),
    (
        "fim da seleção cresce para fora do grafema",
        TEXTO,
        "if (posicao <= alto) fim = posicao;",
        "if (posicao - grafema.length < alto) fim = posicao;",
    ),
    ("utf16 -> pontos devolve o próprio índice", TEXTO, "  return pontos;\n}\n\n/// Posição em pontos", "  return indice;\n}\n\n/// Posição em pontos"),
    ("pontos -> utf16 devolve os pontos", TEXTO, "  return unidades;\n}\n\n/// O mesmo corte", "  return pontos;\n}\n\n/// O mesmo corte"),
    ("formatador deixa passar o \\r", TEXTO, "if (!texto.contains('\\r')) return novo;", "return novo;"),
    (
        "trecho enviado em UTF-16",
        HOJE,
        "Trecho(inicio: trecho.inicioPontos, fim: trecho.fimPontos)",
        "Trecho(inicio: trecho.inicioUtf16, fim: trecho.fimUtf16)",
    ),
    (
        "Voltar também entrega",
        HOJE,
        "if (ok == true && mounted) await _entregar();",
        "if (mounted) await _entregar();",
    ),
    (
        "sem trava de envio repetido",
        HOJE,
        "  Future<void> _entregar() async {\n    if (_enviando) return;\n",
        "  Future<void> _entregar() async {\n",
    ),
    (
        "reenvia fotos que já subiram",
        HOJE,
        "if (foto.idEnviado != null) {\n          continue;",
        "if (false) {\n          continue;",
    ),
    (
        "editar o texto mantém o trecho",
        HOJE,
        "    if (tinhaTrecho) {",
        "    if (false) {",
    ),
    ("mínimo de texto 5", HOJE, "const _textoMinimo = 10;", "const _textoMinimo = 5;"),
    (
        "foto grande demais entra no rascunho",
        HOJE,
        "if (foto.bytes.length > _limiteDaFoto) {",
        "if (false) {",
    ),
    (
        "409 não mostra o registro do dia",
        HOJE,
        "        setState(() => _erroDeEnvio = mensagemDoErro(erro));\n        _carregar();\n        return;",
        "        setState(() => _erroDeEnvio = mensagemDoErro(erro));\n        return;",
    ),
    (
        "trecho marcado em UTF-16 no cartão",
        CARTAO,
        "final inicio = pontosParaUtf16(texto, trecho.inicio);",
        "final inicio = trecho.inicio;",
    ),
    (
        "cartão do parceiro mostra o trecho marcado",
        CARTAO,
        "if (!registro.meu ||\n        trecho == null ||",
        "if (trecho == null ||",
    ),
    (
        "diário passa do mês atual",
        DIARIO,
        "onPressed: _noMesAtual ? null : _seguinte,",
        "onPressed: _seguinte,",
    ),
]


def main() -> None:
    arquivos = {p: p.read_text(encoding="utf-8") for p in (TEXTO, HOJE, CARTAO, DIARIO)}
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
