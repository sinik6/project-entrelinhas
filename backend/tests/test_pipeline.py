"""Testes de contrato do pipeline (design.md, seção 10).

Leem os workflows e o script de deploy como texto: provam que a regra está escrita, não que a VPS a
cumpre. A prova de funcionamento é a evidência do primeiro deploy (validation.md).
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DEPLOY_YML = (RAIZ / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
DEPLOY_SH = (RAIZ / "infra/deploy.sh").read_text(encoding="utf-8")
GITIGNORE = (RAIZ / ".gitignore").read_text(encoding="utf-8")


def test_abu_1_deploy_so_apos_ci_aprovado_na_main():
    """ABU-1 / CTL-1: o deploy automático exige CI com sucesso, em push, na main."""
    assert "workflow_run:" in DEPLOY_YML
    assert "workflows: [CI]" in DEPLOY_YML
    assert "branches: [main]" in DEPLOY_YML
    assert "github.event.workflow_run.conclusion == 'success'" in DEPLOY_YML
    assert "github.event.workflow_run.event == 'push'" in DEPLOY_YML


def test_abu_2_deploy_aborta_sem_segredo():
    """ABU-2: segredo vazio aborta antes de executar o script de publicação."""
    aborta = DEPLOY_YML.index("não configurado no ambiente production")
    publica = DEPLOY_YML.index("bash infra/deploy.sh")

    assert aborta < publica
    assert "DJANGO_SECRET_KEY POSTGRES_PASSWORD" in DEPLOY_YML


def test_ctl_2_segredos_fora_do_rsync():
    """CTL-2 / NFR-SEC-2: .env* fora do Git e do rsync; .env.production com modo 600."""
    assert "--exclude='.env'" in DEPLOY_YML
    assert "--exclude='.env.*'" in DEPLOY_YML
    assert "chmod 600" in DEPLOY_YML
    assert ".env.*" in GITIGNORE


def test_abu_3_deploy_confere_rede_antes_de_parar_a_api():
    """ABU-3 / CTL-6: a rede do proxy é conferida antes de parar a API."""
    assert "set -euo pipefail" in DEPLOY_SH
    confere = DEPLOY_SH.index("docker network inspect traefik_proxy")
    para = DEPLOY_SH.index("dc stop entrelinhas-api")

    assert confere < para


def test_req_3_5_backup_antes_das_migracoes():
    """REQ-3.5 / CTL-6: o backup (pg_dump) vem antes das migrações."""
    backup = DEPLOY_SH.index("pg_dump")
    migra = DEPLOY_SH.index("manage.py migrate")

    assert backup < migra


def test_req_3_6_guarda_so_os_10_backups_mais_novos():
    """REQ-3.6: o script remove do 11º backup em diante."""
    assert "tail -n +11" in DEPLOY_SH


COMPOSE_DEPLOY = (RAIZ / "docker-compose.deploy.yml").read_text(encoding="utf-8")


def test_req_2_4_administrador_entre_migrate_e_subida():
    """REQ-2.4: o administrador é criado depois das migrações e antes de subir a API."""
    migra = DEPLOY_SH.index("manage.py migrate")
    admin = DEPLOY_SH.index("manage.py administrador_inicial")
    sobe = DEPLOY_SH.index("=== Subindo o sistema")

    assert migra < admin < sobe
    assert "set -euo pipefail" in DEPLOY_SH


def test_ctl_4_senha_nao_entra_no_compose_nem_no_servico_da_api():
    """CTL-4 / NFR-SEC-1: a senha só vai ao `run --rm` do comando, nunca ao serviço."""
    assert "SENHA_ADMIN_INICIAL" not in COMPOSE_DEPLOY
    assert "dc run --rm --no-deps -e SENHA_ADMIN_INICIAL" in DEPLOY_SH
    assert "SENHA_ADMIN_INICIAL" in DEPLOY_YML


def test_abu_4_login_do_admin_tem_limite_de_5_por_minuto():
    """ABU-4 / CTL-6: POST no login do Admin passa por limite de 5 por minuto, no domínio e no IP."""
    assert "entrelinhas-login-limite.ratelimit.average: '5'" in COMPOSE_DEPLOY
    assert "entrelinhas-login-limite.ratelimit.period: 1m" in COMPOSE_DEPLOY
    assert "entrelinhas-login-limite.ratelimit.burst: '5'" in COMPOSE_DEPLOY
    for roteador in ("entrelinhas-login-duckdns", "entrelinhas-login-ip"):
        assert f"routers.{roteador}.rule:" in COMPOSE_DEPLOY
        assert f"routers.{roteador}.middlewares: entrelinhas-login-limite@docker" in COMPOSE_DEPLOY
    assert COMPOSE_DEPLOY.count("Method(`POST`) && Path(`/entrelinhas/admin/login/`)") == 2
