"""[010] Contrato da infra dos lembretes: o serviço do disparador, as chaves VAPID, o deploy, o `sw.js` no nginx e o PWA.

Leem os arquivos como texto (e abrem os ícones): provam que a regra está escrita, não que a VPS a cumpre.
"""

import json
import re
import subprocess
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
COMPOSE = (RAIZ / "docker-compose.deploy.yml").read_text(encoding="utf-8")
COMPOSE_DEV = (RAIZ / "compose.yml").read_text(encoding="utf-8")
DEPLOY_SH = (RAIZ / "infra/deploy.sh").read_text(encoding="utf-8")
DEPLOY_YML = (RAIZ / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
NGINX = (RAIZ / "infra/nginx/entrelinhas.conf.template").read_text(encoding="utf-8")
WEB = RAIZ / "frontend/web"


def _servico(compose: str, nome: str) -> str:
    """O bloco de um serviço do compose (do nome até o próximo serviço do mesmo nível)."""
    achado = re.search(rf"^  {re.escape(nome)}:\n((?:    .*\n|\n)+)", compose, re.M)
    assert achado, f"serviço {nome} não encontrado"
    return achado.group(1)


def test_ctl_83_disparador_e_servico_proprio_sem_porta_sem_traefik_e_com_reinicio():
    """[010] CTL-83 / NFR-LEMB-3: mesma imagem da API, outro comando, ninguém chega nele de fora."""
    bloco = _servico(COMPOSE, "entrelinhas-lembretes")

    assert "build: ./backend" in bloco
    assert "command: python manage.py rodar_lembretes" in bloco
    assert "restart: unless-stopped" in bloco
    assert "healthcheck:" in bloco and "lembretes.batimento" in bloco
    assert "ports:" not in bloco
    assert "traefik" not in bloco, "sem rótulos do Traefik e fora da rede do proxy"
    assert "traefik_proxy" not in bloco


def test_ctl_82_84_so_o_disparador_recebe_a_chave_privada_e_as_chaves_sao_obrigatorias():
    """[010] CTL-82 / CTL-84 / NFR-LEMB-1: a API só conhece a pública; faltar chave quebra o compose, não roda sem."""
    disparador = _servico(COMPOSE, "entrelinhas-lembretes")
    api = _servico(COMPOSE, "entrelinhas-api")

    assert "VAPID_PRIVATE_KEY: ${VAPID_PRIVATE_KEY:?" in disparador
    assert "VAPID_PUBLIC_KEY: ${VAPID_PUBLIC_KEY:?" in disparador
    assert "VAPID_ASSUNTO: ${VAPID_ASSUNTO:?" in disparador
    assert "VAPID_PUBLIC_KEY: ${VAPID_PUBLIC_KEY:?" in api
    assert "VAPID_PRIVATE_KEY" not in api
    assert "VAPID_PRIVATE_KEY" not in _servico(COMPOSE, "entrelinhas-web")


def test_ctl_84_deploy_confere_as_chaves_antes_de_parar_a_api_e_nunca_as_imprime():
    """[010] CTL-84: sem as chaves o deploy aborta com a API ainda no ar."""
    conferencia = DEPLOY_SH.index("Conferindo as chaves dos lembretes")
    parada = DEPLOY_SH.index("dc stop entrelinhas-api")
    assert conferencia < parada
    trecho = DEPLOY_SH[conferencia : DEPLOY_SH.index('echo "===', conferencia + 10)]
    for chave in ("VAPID_PRIVATE_KEY", "VAPID_PUBLIC_KEY", "VAPID_ASSUNTO"):
        assert chave in trecho
    assert "echo" not in re.sub(r"echo \"(Faltam|   chaves|===)[^\n]*", "", trecho).replace(
        'echo "Faltam', ""
    ), "o deploy não pode imprimir o valor de uma chave"


def test_ctl_84_workflow_leva_as_chaves_do_ambiente_production_para_o_env():
    """[010] CTL-84: as três chegam como segredos obrigatórios e sem aspa nem quebra de linha."""
    for nome in ("VAPID_PRIVATE_KEY", "VAPID_PUBLIC_KEY", "VAPID_ASSUNTO"):
        assert f"{nome}: ${{{{ secrets.{nome} }}}}" in DEPLOY_YML
    assert re.search(r"for nome in [^;\n]*VAPID_PRIVATE_KEY[^;\n]*; do", DEPLOY_YML)
    assert "VAPID_PRIVATE_KEY" in re.search(r"test\(\"\^\(([^)]*)\)\$\"\)", DEPLOY_YML).group(1)


def test_nfr_lemb_2_nginx_serve_o_sw_sem_cache_e_com_escopo_do_app():
    """[010] NFR-LEMB-2 / T-3.1: `no-cache` e `Service-Worker-Allowed` só no `sw.js`."""
    bloco = re.search(r"location = /sw\.js \{(.*?)\n    \}", NGINX, re.S).group(1)

    assert 'Cache-Control "no-cache"' in bloco
    assert 'Service-Worker-Allowed "./"' in bloco
    assert 'X-Content-Type-Options "nosniff"' in bloco


def test_compose_de_desenvolvimento_tem_o_disparador_com_chaves_opcionais():
    """[010] T-3.2: em desenvolvimento o serviço sobe sem exigir chaves (sem elas os lembretes ficam desligados)."""
    bloco = _servico(COMPOSE_DEV, "lembretes")

    assert "rodar_lembretes" in bloco
    assert ":?" not in bloco


def test_req_18_1_manifesto_completo_e_instalavel():
    """[010] REQ-18.1: nome, ícones de 192 e 512 (comuns e mascaráveis), cores, start_url e escopo relativos ao app."""
    m = json.loads((WEB / "manifest.json").read_text(encoding="utf-8"))

    assert m["name"] == "Entrelinhas" and m["short_name"] == "Entrelinhas"
    assert m["display"] == "standalone" and m["lang"] == "pt-BR"
    assert m["start_url"].startswith("./") and m["scope"] == "./"
    assert re.fullmatch(r"#[0-9A-Fa-f]{6}", m["theme_color"])
    assert re.fullmatch(r"#[0-9A-Fa-f]{6}", m["background_color"])
    por_proposito = {(i["sizes"], i.get("purpose", "any")) for i in m["icons"]}
    assert {
        ("192x192", "any"),
        ("512x512", "any"),
        ("192x192", "maskable"),
        ("512x512", "maskable"),
    } <= por_proposito
    for icone in m["icons"]:
        imagem = Image.open(WEB / icone["src"])
        assert f"{imagem.width}x{imagem.height}" == icone["sizes"], icone["src"]
        assert imagem.format == "PNG"


def test_req_18_1_icones_sao_proprios_e_nao_os_do_modelo_do_flutter():
    """[010] REQ-18.1: o ícone mascarável tem o fundo da marca até a borda (zona segura no meio)."""
    mascara = Image.open(WEB / "icons/Icon-maskable-512.png").convert("RGBA")

    assert mascara.getpixel((2, 2))[:3] == (14, 116, 144)
    assert mascara.getpixel((509, 509))[:3] == (14, 116, 144)
    assert mascara.getpixel((256, 256))[:3] != (14, 116, 144)  # a página no centro


def test_req_18_1_index_aponta_para_o_manifesto_e_registra_o_service_worker_so_para_push():
    """[010] REQ-18.1 / NFR-LEMB-2: o `index.html` liga o manifesto; o registro do service worker é do app (ao ligar o lembrete)."""
    index = (WEB / "index.html").read_text(encoding="utf-8")

    assert 'rel="manifest" href="manifest.json"' in index
    assert "serviceWorker" not in index, (
        "o service worker só é registrado quando a pessoa liga o lembrete"
    )


def test_nfr_lemb_2_sw_nao_usa_rede_nem_cache_nem_banco_no_aparelho():
    """[010] NFR-LEMB-2: varredura do `sw.js`: nada de `fetch`, `caches`, `indexedDB`, `localStorage`, `XMLHttpRequest`."""
    codigo = (WEB / "sw.js").read_text(encoding="utf-8")
    sem_comentarios = re.sub(r"//[^\n]*", "", codigo)

    for proibido in (
        "fetch(",
        "caches",
        "indexedDB",
        "localStorage",
        "XMLHttpRequest",
        "importScripts",
    ):
        assert proibido not in sem_comentarios, proibido


def test_nfr_lemb_2_o_sw_passa_nos_testes_em_node():
    """[010] REQ-19.7 / NFR-LEMB-2: roda `frontend/test_js/sw.test.mjs` com o `node --test` (pulado se não houver Node)."""
    import shutil

    node = shutil.which("node")
    if node is None:
        import pytest

        pytest.skip("Node não está instalado; o teste roda no CI")
    resultado = subprocess.run(
        [node, "--test", str(RAIZ / "frontend/test_js/sw.test.mjs")],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
