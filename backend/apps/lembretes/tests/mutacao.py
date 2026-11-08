"""Roteiro de mutação dos lembretes (spec 010). Não é coletado pelo pytest.

Uso, dentro de `backend/`, com o PostgreSQL de teste de pé:  python apps/lembretes/tests/mutacao.py
"""

import subprocess
from pathlib import Path

DEST = Path("apps/lembretes/destinos.py")
SERV = Path("apps/lembretes/services.py")
DISP = Path("apps/lembretes/disparador.py")
ENVIO = Path("apps/lembretes/envio.py")

MUTANTES = [
    ("aceita http", DEST, 'partes.scheme != "https"', 'partes.scheme not in ("http", "https")'),
    ("aceita IP", DEST, "        return False  # IP, de qualquer tipo", "        pass"),
    ("aceita qualquer porta", DEST, "if porta not in (None, 443):", "if False:"),
    (
        "aceita usuário e senha na URL",
        DEST,
        'or partes.username or partes.password or "@" in partes.netloc',
        "",
    ),
    (
        "sufixo sem ponto",
        DEST,
        'SUFIXOS = (".push.apple.com", ".notify.windows.com")',
        'SUFIXOS = ("push.apple.com", "notify.windows.com")',
    ),
    (
        "host que só termina igual",
        DEST,
        "return host in HOSTS_EXATOS or any(",
        "return any(host.endswith(h) for h in HOSTS_EXATOS) or any(",
    ),
    ("aceita ponto final no host", DEST, 'if not host or host.endswith("."):', "if not host:"),
    ("sem limite de 5", SERV, "APARELHOS_POR_PESSOA = 5", "APARELHOS_POR_PESSOA = 500"),
    ("chave p256dh qualquer tamanho", SERV, "len(p256dh) != 65 or p256dh[0] != 4", "False"),
    ("chave auth qualquer tamanho", SERV, "len(auth) != 16", "False"),
    (
        "remover sem dono",
        SERV,
        "AssinaturaPush.objects.filter(usuario=usuario, endpoint=endpoint).delete()",
        "AssinaturaPush.objects.filter(endpoint=endpoint).delete()",
    ),
    ("janela começa 21h00", DISP, "INICIO = time(21, 30)", "INICIO = time(21, 0)"),
    ("janela termina 23h30", DISP, "FIM = time(23, 0)", "FIM = time(23, 30)"),
    (
        "janela inclusiva no fim",
        DISP,
        "if not INICIO <= local.time() < FIM:",
        "if not INICIO <= local.time() <= FIM:",
    ),
    (
        "quem já entregou recebe",
        DISP,
        "return sorted(com_grupo - entregaram - marcados)",
        "return sorted(com_grupo - marcados)",
    ),
    (
        "sem trava de dia",
        DISP,
        "return sorted(com_grupo - entregaram - marcados)",
        "return sorted(com_grupo - entregaram)",
    ),
    (
        "marca depois de enviar (não é idempotente)",
        DISP,
        "        if not _marcar(usuario_id, hoje):\n            continue\n",
        "        pass\n",
    ),
    (
        "assinatura morta não é removida",
        DISP,
        "                assinatura.delete()\n",
        "                pass\n",
    ),
    (
        "sem grupo recebe",
        DISP,
        "Perfil.objects.filter(pk__in=com_aparelho, grupo__isnull=False)",
        "Perfil.objects.filter(pk__in=com_aparelho)",
    ),
    ("dia pelo UTC", DISP, "hoje = local.date()", "hoje = agora.date()"),
    ("410 não é morta", ENVIO, "if status in (404, 410):", "if status in (404,):"),
    ("sem tempo limite", ENVIO, "timeout=TEMPO_LIMITE,", ""),
    (
        "envia sem conferir o destino",
        ENVIO,
        "if not endpoint_permitido(assinatura.endpoint):",
        "if False:",
    ),
]


def main() -> None:
    originais = {p: p.read_text(encoding="utf-8") for p in (DEST, SERV, DISP, ENVIO)}
    vivos = []
    try:
        for nome, arquivo, antigo, novo in MUTANTES:
            texto = originais[arquivo]
            assert antigo in texto, f"trecho não encontrado: {nome}"
            arquivo.write_text(texto.replace(antigo, novo, 1), encoding="utf-8")
            r = subprocess.run(
                ["uv", "run", "pytest", "apps/lembretes", "-q", "-x", "--no-header"],
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
