"""[004] Contrato da infra das fotos: volume privado, limite de corpo só na rota, backup e limpeza no deploy (CTL-22, CTL-25, NFR-FOTO-1, NFR-FOTO-2).

Leem os arquivos como texto e executam o `deploy.sh` com `docker` falso (mesmo harness da 002): provam que a regra está
escrita e na ordem certa, não que a VPS a cumpre.
"""

import re
from pathlib import Path

# Reusa o harness do deploy da 002 (docker e curl falsos, bash do Git no Windows).
from test_deploy_script import _indice, _rodar, projeto  # noqa: F401

RAIZ = Path(__file__).resolve().parents[2]
COMPOSE = (RAIZ / "docker-compose.deploy.yml").read_text(encoding="utf-8")
COMPOSE_DEV = (RAIZ / "compose.yml").read_text(encoding="utf-8")
NGINX = (RAIZ / "infra/nginx/entrelinhas.conf.template").read_text(encoding="utf-8")
DOCKERFILE_API = (RAIZ / "backend/Dockerfile").read_text(encoding="utf-8")
DEPLOY_SH = (RAIZ / "infra/deploy.sh").read_text(encoding="utf-8")


def _servico(texto: str, nome: str) -> str:
    inicio = texto.index(f"\n  {nome}:\n")
    resto = texto[inicio + 1 :]
    fim = re.search(r"\n  [a-z][\w-]*:\n|\nvolumes:\n", resto[len(nome) + 4 :])
    return resto if fim is None else resto[: fim.start() + len(nome) + 4]


def test_nfr_foto_1_volume_privado_montado_so_na_api_e_incluido_no_compose_de_dev():
    """[004] NFR-FOTO-1: as fotos vão num volume nomeado, montado na API; o proxy do app não o enxerga."""
    api = _servico(COMPOSE, "entrelinhas-api")
    web = _servico(COMPOSE, "entrelinhas-web")

    assert "fotos_data:/data/fotos" in api
    assert "FOTOS_DIR: /data/fotos" in api
    assert re.search(r"^volumes:\n(?:  .*\n)*  fotos_data:", COMPOSE, re.M)
    assert "fotos_data" not in web
    assert "/data/fotos" in COMPOSE_DEV
    assert "FOTOS_DIR" in COMPOSE_DEV


def test_nfr_foto_1_imagem_da_api_cria_a_pasta_com_dono_e_modo_700():
    """[004] CTL-25: a pasta existe na imagem, é do usuário da API e só ele a lê (o volume herda isso na primeira montagem)."""
    assert "/data/fotos" in DOCKERFILE_API
    assert re.search(r"chown\s+(-R\s+)?entrelinhas\s+/data/fotos", DOCKERFILE_API)
    assert re.search(r"chmod\s+700\s+/data/fotos", DOCKERFILE_API)
    # a criação da pasta vem antes de a imagem trocar para o usuário comum
    assert DOCKERFILE_API.index("/data/fotos") < DOCKERFILE_API.index("USER entrelinhas")


def test_nfr_foto_2_limite_de_9_mb_so_na_rota_de_envio_e_o_resto_continua_em_1_mb():
    """[004] CTL-22 / NFR-FOTO-2: `client_max_body_size 9m` só em `location = /api/v1/fotos`."""
    assert re.search(r"client_max_body_size 1m;", NGINX)
    bloco = re.search(r"location = /api/v1/fotos \{(.*?)\n    \}", NGINX, re.S)
    assert bloco is not None, "falta a rota exata do envio de fotos"
    assert "client_max_body_size 9m;" in bloco.group(1)
    assert "proxy_pass http://${API_UPSTREAM};" in bloco.group(1)
    assert "proxy_set_header Host $http_host;" in bloco.group(1)
    assert NGINX.count("client_max_body_size 9m;") == 1
    assert [m for m in re.findall(r"client_max_body_size (\S+);", NGINX)] == ["1m", "9m"]


def test_ctl_25_deploy_copia_o_volume_com_a_api_parada_e_guarda_com_modo_600():
    """[004] CTL-25: o backup do volume sai com a API parada, em arquivo 600, e os mais antigos são podados."""
    assert "dc cp entrelinhas-api:/data/fotos -" in DEPLOY_SH
    assert 'chmod 600 "$backups/fotos-$stamp.tar"' in DEPLOY_SH
    assert "-name 'fotos-*'" in DEPLOY_SH


def test_req_6_9_deploy_executa_limpar_fotos_na_api_ja_no_ar():
    """[004] REQ-6.9: a limpeza roda por `exec` (sem criar contêiner de `run`) depois de subir o sistema."""
    assert "dc exec -T entrelinhas-api python manage.py limpar_fotos" in DEPLOY_SH
    assert DEPLOY_SH.index("up -d --wait --remove-orphans") < DEPLOY_SH.index("limpar_fotos")


def test_ctl_25_ordem_real_do_deploy_parar_copiar_migrar_subir_limpar(projeto):  # noqa: F811
    """[004] CTL-25 / REQ-6.9: executando o `deploy.sh` com `docker` falso, a ordem das chamadas é a prometida."""
    resultado, argv, _ = _rodar(projeto)

    assert resultado.returncode == 0, resultado.stderr
    assert (
        _indice(argv, "stop entrelinhas-api")
        < _indice(argv, "cp entrelinhas-api:/data/fotos -")
        < _indice(argv, "manage.py migrate")
        < _indice(argv, "up -d --wait --remove-orphans")
        < _indice(argv, "exec -T entrelinhas-api python manage.py limpar_fotos")
    )
    backups = projeto[1] / "home/backups/project-entrelinhas"
    assert list(backups.glob("fotos-*.tar")), "o backup das fotos não foi gravado"
