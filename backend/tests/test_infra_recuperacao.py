"""[011] Contrato da infra da recuperação de senha: e-mail obrigatório no deploy, balde de 5 por minuto e segredo fora do git."""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
COMPOSE = (RAIZ / "docker-compose.deploy.yml").read_text(encoding="utf-8")
DEPLOY_SH = (RAIZ / "infra/deploy.sh").read_text(encoding="utf-8")
DEPLOY_YML = (RAIZ / ".github/workflows/deploy.yml").read_text(encoding="utf-8")

VARIAVEIS = (
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "DEFAULT_FROM_EMAIL",
    "APP_URL_BASE",
)


def _api() -> str:
    return re.search(r"^  entrelinhas-api:\n((?:    .*\n|\n)+)", COMPOSE, re.M).group(1)


def test_nfr_rec_4_compose_exige_as_variaveis_de_email_na_api():
    """[011] NFR-REC-4: faltar uma quebra o compose (não sobe sem e-mail)."""
    api = _api()
    for nome in VARIAVEIS:
        assert f"{nome}: ${{{nome}:?" in api, nome


def test_nfr_rec_4_deploy_confere_o_email_antes_de_parar_a_api_e_nunca_imprime_o_valor():
    """[011] NFR-REC-4: sem e-mail o deploy aborta com a API ainda no ar."""
    conferencia = DEPLOY_SH.index("Conferindo o e-mail da recuperação de senha")
    parada = DEPLOY_SH.index("dc stop entrelinhas-api")
    assert conferencia < parada
    trecho = DEPLOY_SH[conferencia:parada]
    for nome in VARIAVEIS:
        assert nome in trecho
    assert '"$chave"' in trecho and 'echo "Falta $chave' in trecho
    assert "$(valor" in trecho and 'echo "$(valor' not in trecho


def test_nfr_rec_1_a_senha_do_smtp_e_segredo_do_github_e_nao_variable():
    """[011] NFR-REC-1: `EMAIL_HOST_PASSWORD` chega como segredo obrigatório, sem aspa nem quebra de linha, e variable com esse nome é erro."""
    assert "EMAIL_HOST_PASSWORD: ${{ secrets.EMAIL_HOST_PASSWORD }}" in DEPLOY_YML
    assert re.search(r"for nome in [^;\n]*EMAIL_HOST_PASSWORD[^;\n]*; do", DEPLOY_YML)
    assert "EMAIL_HOST_PASSWORD" in re.search(r"test\(\"\^\(([^)]*)\)\$\"\)", DEPLOY_YML).group(1)
    # as demais (host, porta, usuário, remetente, base) são variables comuns: não são segredo
    for nome in (
        "EMAIL_HOST",
        "EMAIL_PORT",
        "EMAIL_HOST_USER",
        "DEFAULT_FROM_EMAIL",
        "APP_URL_BASE",
    ):
        assert not re.search(rf"secrets\.{nome}", DEPLOY_YML), nome


def test_ctl_92_abu_25_recuperar_e_redefinir_passam_pelo_balde_de_5_por_minuto():
    """[011] CTL-92 / ABU-25: as duas rotas entram nos roteadores com o limite por origem (domínio e IP), com prioridade acima do app."""
    for roteador in ("entrelinhas-entrar-duckdns", "entrelinhas-entrar-ip"):
        regra = re.search(rf"traefik\.http\.routers\.{roteador}\.rule: (.+)", COMPOSE).group(1)
        assert "Method(`POST`)" in regra
        assert "/entrelinhas/api/v1/auth/recuperacao" in regra
        assert "/entrelinhas/api/v1/auth/redefinir" in regra
        mid = re.search(rf"traefik\.http\.routers\.{roteador}\.middlewares: (.+)", COMPOSE).group(1)
        assert "entrelinhas-entrar-limite@docker" in mid
    assert "entrelinhas-entrar-limite.ratelimit.average: '5'" in COMPOSE
    assert "entrelinhas-entrar-limite.ratelimit.period: 1m" in COMPOSE


def test_ctl_93_deploy_limpa_os_pedidos_antigos():
    """[011] LGPD: retenção de 24 horas, aplicada também no deploy."""
    assert "manage.py limpar_pedidos" in DEPLOY_SH


def test_ctl_94_nao_ha_senha_de_smtp_no_repositorio():
    """[011] NFR-REC-1: nenhum arquivo versionado traz um valor de `EMAIL_HOST_PASSWORD` (só o nome da variável)."""
    for arquivo in (
        list(RAIZ.glob("*.yml"))
        + list(RAIZ.glob("infra/**/*"))
        + list(RAIZ.glob("backend/config/**/*.py"))
    ):
        if arquivo.is_file():
            texto = arquivo.read_text(encoding="utf-8", errors="ignore")
            for achado in re.findall(r"EMAIL_HOST_PASSWORD\s*[:=]\s*['\"]([^'\"$]+)['\"]", texto):
                assert achado == "", f"valor de senha em {arquivo}"
