"""Roteiro de mutação da regra de visibilidade (spec 005, T-2.6). Não é coletado pelo pytest (o nome não começa por `test_`).

Uso, dentro de `backend/` e com o PostgreSQL de teste de pé (ver `specs/steering/tech.md`):
    python apps/registros/tests/mutacao.py
Cada mutante troca um trecho do código por uma versão errada e roda a suíte de `registros` e `fotos`: ela precisa FALHAR
(mutante "MORTO"). Os arquivos originais são restaurados no fim, mesmo com erro. Mutante "VIVO" = regra sem teste.
"""

import subprocess
from pathlib import Path

D = Path("apps/registros/domain.py")
S = Path("apps/registros/services.py")
F = Path("apps/fotos/servicos.py")

MUTANTES = [
    (
        "parcial devolve o texto inteiro",
        D,
        "fatia(registro.texto, registro.trecho_inicio, registro.trecho_fim)",
        "registro.texto",
    ),
    (
        "parcial devolve as fotos",
        D,
        "        fotos_visiveis, aviso = [], None\n",
        "        fotos_visiveis, aviso = list(fotos), None\n",
    ),
    (
        "private devolve o texto",
        D,
        "texto_visivel, fotos_visiveis, aviso = None, [], AVISO_PRIVADO",
        "texto_visivel, fotos_visiveis, aviso = registro.texto, [], AVISO_PRIVADO",
    ),
    (
        "private devolve as fotos",
        D,
        "texto_visivel, fotos_visiveis, aviso = None, [], AVISO_PRIVADO",
        "texto_visivel, fotos_visiveis, aviso = None, list(fotos), AVISO_PRIVADO",
    ),
    (
        "parceiro recebe o trecho",
        D,
        '        "meu": False,\n    }',
        '        "meu": False,\n        "trecho": {"inicio": registro.trecho_inicio, "fim": registro.trecho_fim},\n    }',
    ),
    ("todos veem como autor", D, "if registro.autor_id == usuario_id:", "if True:"),
    (
        "trecho vazio aceito",
        D,
        "0 <= inicio < fim <= len(texto)",
        "0 <= inicio <= fim <= len(texto)",
    ),
    (
        "trecho passa do fim",
        D,
        "0 <= inicio < fim <= len(texto)",
        "0 <= inicio < fim <= len(texto) + 1",
    ),
    (
        "trecho negativo aceito",
        D,
        "0 <= inicio < fim <= len(texto)",
        "-5 <= inicio < fim <= len(texto)",
    ),
    ("minimo de texto 5", D, "TEXTO_MINIMO = 10", "TEXTO_MINIMO = 5"),
    (
        "aceita controle",
        D,
        'if (categoria == "Cc" and caractere not in _PERMITIDOS) or categoria == "Cs":',
        "if False:",
    ),
    ("dia pelo UTC", S, "return instante.astimezone(FUSO).date()", "return instante.date()"),
    ("mes futuro aceito", S, "if (ano, numero) > (hoje.year, hoje.month):", "if False:"),
    (
        "lista sem filtro de grupo",
        S,
        "visiveis |= Q(grupo_id=grupo_id, autor__perfil__grupo_id=grupo_id)",
        "visiveis |= Q(data__gte=inicio)",
    ),
    (
        "lista ignora a saida do autor",
        S,
        "visiveis |= Q(grupo_id=grupo_id, autor__perfil__grupo_id=grupo_id)",
        "visiveis |= Q(grupo_id=grupo_id)",
    ),
    (
        "detalhe sem regra de grupo",
        S,
        "if registro is None or not _pode_ler(registro, usuario):",
        "if registro is None:",
    ),
    (
        "parceiro que saiu ainda le",
        S,
        "        and _grupo_id_de(registro.autor_id) == grupo_id\n",
        "",
    ),
    (
        "foto de outro dono",
        S,
        "            dono=usuario,\n            finalidade=Foto.Finalidade.MANUSCRITO,",
        "            finalidade=Foto.Finalidade.MANUSCRITO,",
    ),
    (
        "aceita foto ja anexada",
        S,
        "            anexada=False,\n            registro__isnull=True,",
        "            registro__isnull=True,",
    ),
    ("sem teto de 3 fotos", S, "not 1 <= len(ids) <= FOTOS_MAXIMO", "not 1 <= len(ids)"),
    ("lista fora de ordem", S, '.order_by("-entregue_em")', '.order_by("entregue_em")'),
    (
        "parceiro ve foto de partial",
        F,
        'registro["visibilidade"] == Registro.Visibilidade.FULL',
        'registro["visibilidade"] != Registro.Visibilidade.PRIVATE',
    ),
    (
        "parceiro ve foto de private",
        F,
        'registro["visibilidade"] == Registro.Visibilidade.FULL',
        "True",
    ),
    ("foto de registro de outro grupo", F, 'and registro["grupo_id"] == grupo', ""),
    ("foto de autor que saiu", F, "            and _grupo_de(foto.dono_id) == grupo\n", ""),
    (
        "limpeza apaga sem reconferir",
        F,
        ".filter(pk=identificador, anexada=False, registro__isnull=True)",
        ".filter(pk=identificador)",
    ),
]


def main() -> None:
    originais = {p: p.read_text(encoding="utf-8") for p in (D, S, F)}
    vivos = []
    try:
        for nome, arquivo, antigo, novo in MUTANTES:
            texto = originais[arquivo]
            assert antigo in texto, f"trecho não encontrado: {nome}"
            arquivo.write_text(texto.replace(antigo, novo, 1), encoding="utf-8")
            r = subprocess.run(
                ["uv", "run", "pytest", "apps/registros", "apps/fotos", "-q", "-x", "--no-header"],
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
