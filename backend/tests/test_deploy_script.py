"""Executa o `infra/deploy.sh` de verdade, com `docker` e `curl` falsos no PATH (spec 002).

O `docker` falso registra os argumentos e o valor da variável da senha que cada chamada recebeu, e pode
falhar numa etapa escolhida. Assim se prova a ordem real das chamadas, que a falha da conferência aborta
antes de parar a API, que a falha da criação para o deploy com a API já parada e que a senha só chega
pelo ambiente, nunca pelos argumentos.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SENHA = "correta-cavalo-bateria-grampo-7"

DOCKER_FALSO = """#!/usr/bin/env bash
printf 'ARGV: %s\\n' "$*" >> "$FAKE_LOG"
printf 'ENV: SENHA=%s\\n' "${SENHA_ADMIN_INICIAL:-<ausente>}" >> "$FAKE_LOG"
case "$*" in
  *"ps --status running --services"*) echo db; exit 0 ;;
  *pg_dump*) echo dump; exit 0 ;;
esac
if [[ "$*" == *"administrador_inicial --verificar"* && "${FALHA:-}" == verificar ]]; then exit 1; fi
if [[ "$*" == *"administrador_inicial"* && "$*" != *"--verificar"* && "${FALHA:-}" == criar ]]; then exit 1; fi
exit 0
"""

CURL_FALSO = """#!/usr/bin/env bash
case "$*" in
  *"--write-out"*) printf '301 https://217.216.82.25/entrelinhas/admin/login/' ;;
esac
exit 0
"""

ENV_PRODUCTION = (
    f"ADMIN_USUARIO='dono'\r\nADMIN_EMAIL='dono@example.com'\r\nSENHA_ADMIN_INICIAL='{SENHA}'\r\n"
)


@pytest.fixture
def projeto(tmp_path):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash não encontrado")
    (tmp_path / "infra").mkdir()
    shutil.copy(RAIZ / "infra/deploy.sh", tmp_path / "infra/deploy.sh")
    (tmp_path / ".env.production").write_bytes(ENV_PRODUCTION.encode())
    (tmp_path / "bin").mkdir()
    for nome, conteudo in (("docker", DOCKER_FALSO), ("curl", CURL_FALSO)):
        arquivo = tmp_path / "bin" / nome
        arquivo.write_bytes(conteudo.encode())
        arquivo.chmod(0o755)
    (tmp_path / "home").mkdir()
    return bash, tmp_path


def _rodar(projeto, falha=""):
    bash, pasta = projeto
    # cygpath existe no Git Bash do Windows e converte caminhos; no Linux o `|| echo` devolve o próprio caminho.
    wrapper = (
        'conv() { cygpath -u "$1" 2>/dev/null || echo "$1"; }; '
        'export PATH="$(conv "$FAKE_BIN"):$PATH" HOME="$(conv "$FAKE_HOME")" FAKE_LOG="$(conv "$FAKE_LOG")"; '
        "bash infra/deploy.sh"
    )
    log = pasta / "chamadas.log"
    resultado = subprocess.run(
        [bash, "-c", wrapper],
        cwd=pasta,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={
            **os.environ,
            "FAKE_BIN": str(pasta / "bin"),
            "FAKE_HOME": str(pasta / "home"),
            "FAKE_LOG": str(log),
            "FALHA": falha,
        },
    )
    texto = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    argv = [linha[6:] for linha in texto.splitlines() if linha.startswith("ARGV: ")]
    ambiente = [linha[5:] for linha in texto.splitlines() if linha.startswith("ENV: ")]
    return resultado, argv, ambiente


def _indice(argv, trecho):
    return next(i for i, linha in enumerate(argv) if trecho in linha)


def test_req_2_5_deploy_ok_chama_na_ordem_certa_e_a_senha_so_vai_pelo_ambiente(projeto):
    """[002] REQ-2.4 / REQ-2.5 / CTL-4 / CTL-10: ordem real das chamadas e senha fora dos argumentos."""
    resultado, argv, ambiente = _rodar(projeto)

    assert resultado.returncode == 0, resultado.stderr
    verificar = _indice(argv, "administrador_inicial --verificar")
    cria = next(i for i, a in enumerate(argv) if a.endswith("administrador_inicial"))
    assert (
        _indice(argv, " build")
        < verificar
        < _indice(argv, "stop entrelinhas-api")
        < _indice(argv, "manage.py migrate")
        < cria
        < _indice(argv, "up -d --wait --remove-orphans")
    )
    assert not any(SENHA in linha for linha in argv), (
        "a senha apareceu nos argumentos de uma chamada"
    )
    # só as duas chamadas do administrador recebem a senha no ambiente; o resto do deploy não a vê
    recebem = [i for i, a in enumerate(argv) if "administrador_inicial" in a]
    for i, valor in enumerate(ambiente):
        assert (SENHA in valor) == (i in recebem), f"chamada {i}: {argv[i]} -> {valor}"


def test_req_2_5_todo_run_do_deploy_sai_sem_rotulos_do_traefik(projeto):
    """[002] CTL-10: o contêiner de `run` não entra no balanceador (daria 502 no Admin com a API no ar)."""
    resultado, argv, _ = _rodar(projeto)

    runs = [a for a in argv if " run " in f" {a} "]
    assert resultado.returncode == 0
    assert len(runs) == 3  # verificar, migrate, criar
    assert all("-l traefik.enable=false" in a for a in runs)


def test_req_2_5_conferencia_recusada_aborta_antes_de_parar_a_api(projeto):
    """[002] REQ-2.5 / CTL-10: senha recusada na conferência termina o deploy sem `stop` e sem `up`."""
    resultado, argv, _ = _rodar(projeto, falha="verificar")

    assert resultado.returncode != 0
    assert not any("stop entrelinhas-api" in a for a in argv)
    assert not any("manage.py migrate" in a for a in argv)
    assert not any("--remove-orphans" in a for a in argv)


def test_req_2_4_criacao_recusada_aborta_com_a_api_parada(projeto):
    """[002] REQ-2.4: recusa na criação (depois do `stop`) termina o deploy e a API não volta a subir."""
    resultado, argv, _ = _rodar(projeto, falha="criar")

    assert resultado.returncode != 0
    assert any("stop entrelinhas-api" in a for a in argv)
    assert any("manage.py migrate" in a for a in argv)
    assert not any("--remove-orphans" in a for a in argv)
