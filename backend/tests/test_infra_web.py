"""[003] Contrato da infra do front: nginx, compose, Traefik, SDK do Flutter e dependências (ABU-1, CTL-11, CTL-19, CTL-20).

Leem os arquivos como texto: provam que a regra está escrita, não que o Traefik ou a VPS a cumprem
(o limite de login é medido no ar, na T-4.2).
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
COMPOSE = (RAIZ / "docker-compose.deploy.yml").read_text(encoding="utf-8")
NGINX = (RAIZ / "infra/nginx/entrelinhas.conf.template").read_text(encoding="utf-8")
WEB_DOCKERFILE = (RAIZ / "infra/web.Dockerfile").read_text(encoding="utf-8")
SDK_DOCKERFILE = (RAIZ / "frontend/Dockerfile").read_text(encoding="utf-8")
PUBSPEC = (RAIZ / "frontend/pubspec.yaml").read_text(encoding="utf-8")
DEPLOY_SH = (RAIZ / "infra/deploy.sh").read_text(encoding="utf-8")
CI = (RAIZ / ".github/workflows/ci.yml").read_text(encoding="utf-8")


def _rotulos():
    """Rótulos Traefik do compose agrupados por roteador."""
    rotulos = {}
    for roteador, chave, valor in re.findall(
        r"traefik\.http\.routers\.(entrelinhas-[a-z-]+)\.([a-z.]+): (.+)", COMPOSE
    ):
        rotulos.setdefault(roteador, {})[chave] = valor.strip().strip("'")
    return rotulos


def test_abu_1_entrar_e_aceitar_convite_tem_balde_de_5_fichas_por_minuto():
    """[003] ABU-1 / CTL-11: o POST de entrar e o de aceitar convite passam por balde de 5 fichas, no domínio e no IP."""
    assert "entrelinhas-entrar-limite.ratelimit.average: '5'" in COMPOSE
    assert "entrelinhas-entrar-limite.ratelimit.period: 1m" in COMPOSE
    assert "entrelinhas-entrar-limite.ratelimit.burst: '5'" in COMPOSE

    rotulos = _rotulos()
    web_domino, web_ip = (
        int(rotulos["entrelinhas-web-duckdns"]["priority"]),
        int(rotulos["entrelinhas-web-ip"]["priority"]),
    )
    for roteador, host, web in (
        ("entrelinhas-entrar-duckdns", "jpsys.duckdns.org", web_domino),
        ("entrelinhas-entrar-ip", "217.216.82.25", web_ip),
    ):
        limite = rotulos[roteador]
        assert f"Host(`{host}`)" in limite["rule"]
        assert "Method(`POST`)" in limite["rule"]
        assert "/entrelinhas/api/v1/auth/entrar" in limite["rule"]
        assert "/entrelinhas/api/v1/convites/aceitar" in limite["rule"]
        assert int(limite["priority"]) > web, "o roteador do limite precisa vencer o do app"
        assert limite["service"] == "entrelinhas-web"
        assert limite["entrypoints"] == "websecure"
        assert limite["tls"] == "true"
        assert "entrelinhas-entrar-limite@docker" in limite["middlewares"]
        assert "entrelinhas-prefixo@docker" in limite["middlewares"]
        assert "secure-headers@file" in limite["middlewares"]


def test_ctl_11_servico_web_tem_nome_unico_sem_porta_publicada_e_o_app_vence_so_o_prefixo():
    """[003] CTL-11 / D-1: `entrelinhas-web` está na rede do proxy, não publica porta e o app fica abaixo do Admin."""
    assert re.search(r"^  entrelinhas-web:\n", COMPOSE, re.M)
    bloco = COMPOSE[COMPOSE.index("  entrelinhas-web:") :]
    bloco = bloco[: bloco.index("\nvolumes:")]
    assert "ports:" not in bloco
    assert "traefik_proxy" in bloco
    assert "healthcheck:" in bloco
    assert "entrelinhas-prefixo.stripprefix.prefixes: /entrelinhas" in COMPOSE
    rotulos = _rotulos()
    for web, admin in (
        ("entrelinhas-web-duckdns", "entrelinhas-admin-duckdns"),
        ("entrelinhas-web-ip", "entrelinhas-admin-ip"),
    ):
        assert int(rotulos[web]["priority"]) < int(rotulos[admin]["priority"]), (
            "o Admin não pode cair no app"
        )
        assert rotulos[web]["service"] == "entrelinhas-web"
        assert "entrelinhas-prefixo@docker" in rotulos[web]["middlewares"]


def test_ctl_19_nginx_tem_csp_restritivo_e_so_repassa_a_api():
    """[003] CTL-19: CSP sem origem externa, sem `unsafe-eval`, sem moldura, e `/api/` repassado à API interna."""
    csp = re.search(r'Content-Security-Policy "([^"]+)"', NGINX).group(1)
    assert "default-src 'self'" in csp
    assert "script-src 'self' 'wasm-unsafe-eval'" in csp
    assert "connect-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src" not in csp or "object-src 'none'" in csp
    assert "unsafe-eval'" not in csp.replace("wasm-unsafe-eval'", "")
    assert "http:" not in csp and "https:" not in csp and "*" not in csp
    assert 'add_header X-Content-Type-Options "nosniff" always;' in NGINX
    assert "Referrer-Policy" in NGINX
    assert "server_tokens off;" in NGINX
    assert re.search(r"location /api/ \{[^}]*proxy_pass http://\$\{API_UPSTREAM\};", NGINX, re.S)
    assert "proxy_set_header Host $http_host;" in NGINX
    assert "proxy_set_header X-Forwarded-Proto $proto_original;" in NGINX


def test_ctl_19_build_do_flutter_sem_cdn():
    """[003] CTL-19: o app é compilado sem CDN, com o prefixo da VPS e a API na mesma origem."""
    assert "--no-web-resources-cdn" in WEB_DOCKERFILE
    assert '--base-href "${BASE_HREF}"' in WEB_DOCKERFILE
    assert "--dart-define=API_BASE" in WEB_DOCKERFILE
    assert "BASE_HREF: /entrelinhas/" in COMPOSE
    assert "API_BASE: /entrelinhas/api/v1" in COMPOSE


def test_ctl_20_sdk_do_flutter_vem_com_sha256_conferido():
    """[003] CTL-20: o SDK é baixado com versão fixa e o SHA-256 é conferido no build."""
    assert re.search(r"ARG FLUTTER_VERSAO=\d+\.\d+\.\d+", SDK_DOCKERFILE)
    assert re.search(r"ARG FLUTTER_SHA256=[0-9a-f]{64}\b", SDK_DOCKERFILE)
    assert "sha256sum -c -" in SDK_DOCKERFILE


def test_ctl_20_pacotes_do_front_sao_so_os_do_adr_0005():
    """[003] CTL-20: pacote novo exige ADR; `pubspec.yaml` só pode ter os do ADR-0005, e o `pubspec.lock` é versionado."""
    secao = lambda nome: re.search(rf"^{nome}:\n((?:  .*\n|\n)+)", PUBSPEC, re.M).group(1)  # noqa: E731
    pacotes = set(re.findall(r"^  ([a-z_]+):", secao("dependencies"), re.M))
    dev = set(re.findall(r"^  ([a-z_]+):", secao("dev_dependencies"), re.M))

    assert pacotes == {"flutter", "dio", "flutter_riverpod", "go_router", "image_picker"}
    assert dev == {"flutter_test", "flutter_lints", "mocktail"}
    assert (RAIZ / "frontend/pubspec.lock").exists()


def test_ctl_20_deploy_e_ci_constroem_o_sdk_e_rodam_analyze_e_test():
    """[003] CTL-20: o deploy constrói a imagem do SDK antes do web, e o CI roda `flutter analyze` e `flutter test`."""
    sdk = DEPLOY_SH.index("docker build -t entrelinhas-flutter-sdk:local frontend")
    web = DEPLOY_SH.index("dc build")
    assert sdk < web
    assert "flutter analyze" in CI
    assert "flutter test" in CI
    assert "entrelinhas-flutter-sdk" in CI
