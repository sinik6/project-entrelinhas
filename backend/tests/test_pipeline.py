"""Testes de contrato do pipeline (design.md, seção 10).

Leem os workflows, o compose e o script de deploy como texto: provam que a regra está escrita, não que a
VPS a cumpre. O comportamento do `deploy.sh` (com `docker` falso) e do bloco do workflow (com `jq`) é
executado de verdade em `test_deploy_script.py` e `test_workflow_env.py`.

Os IDs de cada teste levam a marca da mudança de origem ([001] ou [002]), porque REQ, ABU e CTL são
provisórios dentro de cada mudança e se repetem entre elas até o arquivamento dar IDs permanentes. O
`sdd_lint` não separa as mudanças: um ID citado por um teste da 001 também conta como coberto na 002.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
DEPLOY_YML = (RAIZ / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
DEPLOY_SH = (RAIZ / "infra/deploy.sh").read_text(encoding="utf-8")
GITIGNORE = (RAIZ / ".gitignore").read_text(encoding="utf-8")
COMPOSE_DEPLOY = (RAIZ / "docker-compose.deploy.yml").read_text(encoding="utf-8")


def _comandos(texto):
    """Linhas de comando do script, sem comentários nem linhas em branco."""
    return [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip() and not linha.strip().startswith("#")
    ]


def _posicao(comandos, prefixo):
    return next(i for i, linha in enumerate(comandos) if linha.startswith(prefixo))


def test_abu_1_deploy_so_apos_ci_aprovado_na_main():
    """[001] ABU-1 / CTL-1: o deploy automático exige CI com sucesso, em push, na main."""
    assert "workflow_run:" in DEPLOY_YML
    assert "workflows: [CI]" in DEPLOY_YML
    assert "branches: [main]" in DEPLOY_YML
    assert "github.event.workflow_run.conclusion == 'success'" in DEPLOY_YML
    assert "github.event.workflow_run.event == 'push'" in DEPLOY_YML


def test_abu_2_deploy_aborta_sem_segredo():
    """[001] ABU-2: segredo vazio aborta antes de executar o script de publicação."""
    aborta = DEPLOY_YML.index("não configurado no ambiente production")
    publica = DEPLOY_YML.index("bash infra/deploy.sh")

    assert aborta < publica
    assert "DJANGO_SECRET_KEY POSTGRES_PASSWORD" in DEPLOY_YML


def test_ctl_2_segredos_fora_do_rsync():
    """[001] CTL-2 / NFR-SEC-2: .env* fora do Git e do rsync; .env.production com modo 600."""
    assert "--exclude='.env'" in DEPLOY_YML
    assert "--exclude='.env.*'" in DEPLOY_YML
    assert "chmod 600 ~/${{ env.APP_NAME }}/.env.production" in DEPLOY_YML
    assert ".env.*" in GITIGNORE


def test_abu_3_deploy_confere_rede_antes_de_parar_a_api():
    """[001] ABU-3 / CTL-6: a rede do proxy é conferida antes de parar a API."""
    assert "set -euo pipefail" in DEPLOY_SH
    confere = DEPLOY_SH.index("docker network inspect traefik_proxy")
    para = DEPLOY_SH.index("dc stop entrelinhas-api")

    assert confere < para


def test_req_3_5_backup_antes_das_migracoes():
    """[001] REQ-3.5 / CTL-6: o backup (pg_dump) vem antes das migrações."""
    backup = DEPLOY_SH.index("pg_dump")
    migra = DEPLOY_SH.index("manage.py migrate")

    assert backup < migra


def test_req_3_6_guarda_so_os_10_backups_mais_novos():
    """[001] REQ-3.6: o script remove do 11º backup em diante."""
    assert "tail -n +11" in DEPLOY_SH


def test_req_2_4_administrador_entre_migrate_e_subida():
    """[002] REQ-2.4: o administrador é criado depois das migrações e antes de subir a API."""
    comandos = _comandos(DEPLOY_SH)

    migra = _posicao(
        comandos,
        "dc run --rm --no-deps -l traefik.enable=false entrelinhas-api python manage.py migrate",
    )
    admin = comandos.index("admin_inicial")
    sobe = _posicao(comandos, "dc up -d --wait --remove-orphans")

    assert migra < admin < sobe
    assert "set -euo pipefail" in comandos


def test_req_2_5_chamadas_do_administrador_sao_linhas_proprias_sem_or_true():
    """[002] REQ-2.4 / REQ-2.5 / CTL-10: as duas chamadas são comandos ativos que, ao falhar, abortam o deploy."""
    comandos = _comandos(DEPLOY_SH)

    assert "admin_inicial --verificar" in comandos
    assert "admin_inicial" in comandos
    assert not any("||" in linha for linha in comandos if linha.startswith("admin_inicial"))
    constroi = _posicao(comandos, "dc build")
    confere = comandos.index("admin_inicial --verificar")
    para = _posicao(comandos, "dc stop entrelinhas-api")
    assert constroi < confere < para


def test_ctl_10_todo_run_do_deploy_desliga_os_rotulos_do_traefik():
    """[002] CTL-10: o contêiner de `run` não pode entrar no balanceador do Traefik (daria 502 no Admin)."""
    corpo = DEPLOY_SH.replace("\\\n", " ")
    chamadas = [
        linha
        for linha in corpo.splitlines()
        if "dc run" in linha and not linha.lstrip().startswith("#")
    ]

    assert len(chamadas) == 2
    assert all("-l traefik.enable=false" in linha for linha in chamadas)


def test_ctl_4_senha_nao_entra_no_compose_nem_no_servico_da_api():
    """[002] CTL-4 / NFR-SEC-1: a senha só vai ao `run --rm` do comando, nunca ao serviço nem ao argv."""
    assert "SENHA_ADMIN_INICIAL" not in COMPOSE_DEPLOY
    assert "env_file" not in COMPOSE_DEPLOY
    corpo = DEPLOY_SH.replace("\\\n", " ")
    run_admin = next(linha for linha in corpo.splitlines() if "-e SENHA_ADMIN_INICIAL" in linha)
    assert re.search(r"-e SENHA_ADMIN_INICIAL(?![=\w])", run_admin)
    assert "-e SENHA_ADMIN_INICIAL=" not in corpo
    assert "for nome in DJANGO_SECRET_KEY POSTGRES_PASSWORD SENHA_ADMIN_INICIAL; do" in DEPLOY_YML


def test_ctl_8_workflow_grava_com_aspas_simples_e_recusa_aspa_no_valor():
    """[002] CTL-8 / NFR-SEC-1: o .env.production sai com aspas simples (o Compose não interpola `$`)."""
    gravacao = 'printf "%s=\'%s\'\\n" "$nome" "$valor"'

    assert gravacao in DEPLOY_YML
    assert "contém aspa simples" in DEPLOY_YML
    assert "APP_NAME=$APP_NAME" not in DEPLOY_YML
    assert "umask 077" in DEPLOY_YML
    assert "chmod 600 ~/${{ env.APP_NAME }}/.env.production" in DEPLOY_YML
    assert DEPLOY_YML.index("> /tmp/.env.production") < DEPLOY_YML.index(">> /tmp/.env.production")


def test_ctl_8_nenhum_comando_imprime_a_senha():
    """[002] CTL-8 / NFR-SEC-1: nenhum echo/printf do workflow ou do deploy.sh escreve a senha, e não há `set -x`."""
    for nome, texto in (("deploy.yml", DEPLOY_YML), ("deploy.sh", DEPLOY_SH)):
        assert "set -x" not in texto, nome
        for linha in _comandos(texto):
            imprime = linha.startswith(("echo", "printf", "cat ", "tee "))
            if imprime and "SENHA_ADMIN_INICIAL" in linha:
                pytest.fail(f"{nome}: comando imprime a senha: {linha}")
            if imprime and '"$valor"' in linha and ">> /tmp/.env.production" not in linha:
                pytest.fail(f"{nome}: comando imprime um segredo: {linha}")


def test_ctl_9_variables_chegam_por_env_e_nao_dentro_do_texto_do_script():
    """[002] CTL-9: `toJSON(vars)` vai em `env:` do passo, nunca dentro do texto do script (injeção por aspa)."""
    assert "echo '${{ toJSON(vars) }}'" not in DEPLOY_YML
    assert "VARS_JSON: ${{ toJSON(vars) }}" in DEPLOY_YML
    assert DEPLOY_YML.count("${{ toJSON(vars) }}") == 1


def test_ctl_9_variable_com_nome_de_segredo_e_recusada():
    """[002] CTL-9: uma variable chamada como um segredo derruba o passo, em vez de prevalecer sobre o segredo."""
    assert "DJANGO_SECRET_KEY|POSTGRES_PASSWORD|SENHA_ADMIN_INICIAL" in DEPLOY_YML
    assert "variable com nome de segredo" in DEPLOY_YML


def test_ctl_9_valor_usa_a_ultima_ocorrencia(tmp_path):
    """[002] CTL-9: se um nome aparece duas vezes, vale a última (a do segredo, que o workflow grava depois)."""
    env = "SENHA_ADMIN_INICIAL='da-variable'\nSENHA_ADMIN_INICIAL='do-segredo'\n"

    assert _valor(tmp_path, env, "SENHA_ADMIN_INICIAL") == "do-segredo"


def test_ctl_8_valor_devolve_a_senha_crua_com_cifrao_e_aspas(tmp_path):
    """[002] CTL-8 / NFR-SEC-1: `valor()` devolve a senha exata (com `$`) do arquivo escrito com aspas simples."""
    env = "A='x'\r\nSENHA_ADMIN_INICIAL='Abc$Segredo123xyz'\r\n"

    assert _valor(tmp_path, env, "SENHA_ADMIN_INICIAL") == "Abc$Segredo123xyz"
    assert _valor(tmp_path, env, "AUSENTE") == ""


def _valor(tmp_path, conteudo, nome):
    """Executa a função `valor()` do deploy.sh de verdade (bash) sobre um .env.production de teste."""
    # `shutil.which`, e não "bash" solto: no Windows o CreateProcess acha primeiro o bash do WSL (System32),
    # que não enxerga o diretório temporário. O CI (Linux) resolve para /usr/bin/bash.
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash não encontrado")
    funcao = next(linha for linha in DEPLOY_SH.splitlines() if linha.startswith("valor() {"))
    (tmp_path / ".env.production").write_bytes(conteudo.encode())
    resultado = subprocess.run(
        [bash, "-c", f"set -euo pipefail; {funcao}; valor {nome}"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return resultado.stdout.rstrip("\n")


def _rotulos_de_login():
    """Rótulos Traefik dos roteadores de login, por roteador, e a prioridade do roteador do Admin."""
    rotulos = {}
    for roteador, chave, valor in re.findall(
        r"traefik\.http\.routers\.(entrelinhas-[a-z-]+)\.([a-z.]+): (.+)", COMPOSE_DEPLOY
    ):
        rotulos.setdefault(roteador, {})[chave] = valor.strip().strip("'")
    return rotulos


def test_abu_4_login_do_admin_tem_balde_de_5_fichas_por_minuto():
    """[002] ABU-4 / CTL-6: POST no login do Admin passa por balde de 5 fichas, no domínio e no IP."""
    assert "entrelinhas-login-limite.ratelimit.average: '5'" in COMPOSE_DEPLOY
    assert "entrelinhas-login-limite.ratelimit.period: 1m" in COMPOSE_DEPLOY
    assert "entrelinhas-login-limite.ratelimit.burst: '5'" in COMPOSE_DEPLOY

    rotulos = _rotulos_de_login()
    admin_domino = int(rotulos["entrelinhas-admin-duckdns"]["priority"])
    admin_ip = int(rotulos["entrelinhas-admin-ip"]["priority"])
    for roteador, host, admin in (
        ("entrelinhas-login-duckdns", "jpsys.duckdns.org", admin_domino),
        ("entrelinhas-login-ip", "217.216.82.25", admin_ip),
    ):
        login = rotulos[roteador]
        assert f"Host(`{host}`)" in login["rule"]
        assert "Method(`POST`) && Path(`/entrelinhas/admin/login/`)" in login["rule"]
        assert int(login["priority"]) > admin, "o roteador de login precisa vencer o do Admin"
        assert login["service"] == "entrelinhas-api"
        assert login["entrypoints"] == "websecure"
        assert login["tls"] == "true"
        assert "entrelinhas-login-limite@docker" in login["middlewares"]
        assert "secure-headers@file" in login["middlewares"]
