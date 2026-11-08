"""Roteiro de mutação da recuperação de senha (spec 011). Não é coletado pelo pytest.

Uso, dentro de `backend/`, com o PostgreSQL de teste de pé:  python apps/acesso/tests/mutacao_recuperacao.py
"""

import subprocess
from pathlib import Path

R = Path("apps/acesso/recuperacao.py")
V = Path("apps/acesso/views.py")

# Equivalentes (descartados): minúsculas e validação do formato do e-mail (a busca é `iexact`, e um e-mail ruim nunca acha conta);
# a resposta "diferente sem conta" não era um mutante real (`pedir` devolve sempre `None`).
MUTANTES = [
    ("limite de 3 vira 300", R, "LIMITE_POR_HORA = 3", "LIMITE_POR_HORA = 300"),
    (
        "limite por hora vira por dia",
        R,
        "criado_em__gte=instante - timedelta(hours=1)",
        "criado_em__gte=instante - timedelta(hours=30)",
    ),
    (
        "e-mail sem normalizar (minúsculas)",
        R,
        "email = email.strip().lower()",
        "email = email.strip()",
    ),
    ("e-mail sem tirar espaços", R, "email = email.strip().lower()", "email = email.lower()"),
    (
        "e-mail sem validar o formato",
        R,
        "        validate_email(email)\n    except ValidationError:\n        return\n",
        "        pass\n    except ValidationError:\n        return\n",
    ),
    (
        "conta inativa recebe",
        R,
        "objects.filter(email__iexact=email, is_active=True)",
        "objects.filter(email__iexact=email)",
    ),
    (
        "link com a base do pedido (Host)",
        R,
        "return f\"{settings.APP_URL_BASE.rstrip('/')}/#/redefinir/{uid}/{token}\"",
        "return f\"{settings.APP_URL_BASE.rstrip('/')}/?uid={uid}&token={token}\"",
    ),
    (
        "envio dentro do pedido (síncrono)",
        R,
        "    t = threading.Thread(target=tarefa, daemon=True)\n    _threads.append(t)\n    t.start()",
        "    tarefa()",
    ),
    (
        "log com o tipo e a mensagem do erro",
        R,
        'log.error("envio do e-mail de recuperacao falhou tipo=%s", type(erro).__name__)',
        'log.error("envio do e-mail de recuperacao falhou: %s", erro)',
    ),
    ("token não é conferido", R, "or not default_token_generator.check_token(usuario, token)", ""),
    ("uid de conta inativa vale", R, "        or not usuario.is_active\n", ""),
    (
        "senha sem política",
        R,
        "        validate_password(nova_senha, user=usuario)",
        "        pass",
    ),
    (
        "sem e-mail de aviso",
        R,
        '    _enviar_em_segundo_plano(\n        usuario.email,\n        "Entrelinhas — sua senha foi alterada",',
        '    (lambda *a: None)(\n        usuario.email,\n        "Entrelinhas — sua senha foi alterada",',
    ),
    ("sessões da conta não são encerradas", R, "    _encerrar_sessoes(usuario)\n", ""),
    (
        "pedidos antigos não são apagados",
        R,
        "PedidoRecuperacao.objects.filter(\n            usuario=usuario, criado_em__lt=instante - RETENCAO\n        ).delete()",
        "pass",
    ),
]


def main() -> None:
    originais = {p: p.read_text(encoding="utf-8") for p in (R, V)}
    vivos = []
    try:
        for nome, arquivo, antigo, novo in MUTANTES:
            texto = originais[arquivo]
            if antigo not in texto:
                print(f"TRECHO NÃO ENCONTRADO: {nome}", flush=True)
                vivos.append(nome + " (trecho não encontrado)")
                continue
            arquivo.write_text(texto.replace(antigo, novo, 1), encoding="utf-8")
            r = subprocess.run(
                [
                    "uv",
                    "run",
                    "pytest",
                    "apps/acesso/tests/test_recuperacao.py",
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
