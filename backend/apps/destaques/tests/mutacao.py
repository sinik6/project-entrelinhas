"""Roteiro de mutação dos destaques (spec 007, T-2.6). Não é coletado pelo pytest.

Uso, dentro de `backend/`, com o PostgreSQL de teste de pé:  python apps/destaques/tests/mutacao.py
Cada mutante troca um trecho por uma versão errada e roda a suíte dos destaques: ela precisa FALHAR ("MORTO").
"""

import subprocess
from pathlib import Path

S = Path("apps/destaques/services.py")
D = Path("apps/registros/domain.py")

MUTANTES = [
    (
        "posição passa do visível em 1",
        S,
        "0 <= inicio < fim <= len(visivel)",
        "0 <= inicio < fim <= len(visivel) + 1",
    ),
    (
        "posição negativa aceita",
        S,
        "0 <= inicio < fim <= len(visivel)",
        "-5 <= inicio < fim <= len(visivel)",
    ),
    (
        "início igual ao fim aceito",
        S,
        "0 <= inicio < fim <= len(visivel)",
        "0 <= inicio <= fim <= len(visivel)",
    ),
    (
        "bool aceito como inteiro",
        S,
        "isinstance(valor, int) and not isinstance(valor, bool)",
        "isinstance(valor, int)",
    ),
    (
        "mensagem cita o tamanho a mais",
        S,
        "entre 0 e {len(visivel)}",
        "entre 0 e {len(visivel) + 1000}",
    ),
    (
        "partial devolve o texto inteiro",
        D,
        "        return fatia(registro.texto, registro.trecho_inicio, registro.trecho_fim)\n    return None",
        "        return registro.texto\n    return None",
    ),
    (
        "private tem texto visível",
        D,
        '    if registro.visibilidade == "partial":\n        return fatia(registro.texto, registro.trecho_inicio, registro.trecho_fim)\n    return None',
        '    if registro.visibilidade == "partial":\n        return fatia(registro.texto, registro.trecho_inicio, registro.trecho_fim)\n    return registro.texto',
    ),
    ("limite de 50 vira 5000", S, "DESTAQUES_POR_PESSOA = 50", "DESTAQUES_POR_PESSOA = 5000"),
    (
        "limite de 20 vira 2000",
        S,
        "COMENTARIOS_POR_DESTAQUE = 20",
        "COMENTARIOS_POR_DESTAQUE = 2000",
    ),
    (
        "sem trava no registro",
        S,
        "Registro.objects.select_for_update().filter(pk=registro.pk).first()",
        "pass",
    ),
    (
        "sem trava no destaque",
        S,
        "Destaque.objects.select_for_update().filter(pk=destaque.pk).first()",
        "pass",
    ),
    (
        "apagar destaque de outro",
        S,
        "    destaque = _destaque_do_grupo(usuario, destaque_id)\n    if destaque.autor_id != usuario.pk:",
        "    destaque = _destaque_do_grupo(usuario, destaque_id)\n    if False:",
    ),
    (
        "editar comentário de outro",
        S,
        "    comentario = _comentario_do_grupo(usuario, comentario_id)\n    if comentario.autor_id != usuario.pk:\n        raise ErroProibido\n    comentario.texto",
        "    comentario = _comentario_do_grupo(usuario, comentario_id)\n    comentario.texto",
    ),
    (
        "apagar comentário de outro",
        S,
        "    if comentario.autor_id != usuario.pk:\n        raise ErroProibido\n    comentario.delete()",
        "    comentario.delete()",
    ),
    (
        "destaque de outro grupo sem 404",
        S,
        "    registro_legivel(usuario, destaque.registro_id)  # 404",
        "    pass  # 404",
    ),
    (
        "comentário de outro grupo sem 404",
        S,
        "    registro_legivel(usuario, comentario.destaque.registro_id)",
        "    pass",
    ),
    ("comentário de 1001 aceito", S, "COMENTARIO_MAXIMO = 1000", "COMENTARIO_MAXIMO = 100000"),
    ("comentário só de espaços aceito", S, "not texto.strip()", "False"),
]


def main() -> None:
    originais = {p: p.read_text(encoding="utf-8") for p in (S, D)}
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
                    "apps/destaques",
                    "apps/registros",
                    "-q",
                    "-x",
                    "--no-header",
                ],
                capture_output=True,
                text=True,
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
