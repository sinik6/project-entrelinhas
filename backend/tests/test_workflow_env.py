"""Executa o bloco real do workflow que gera o .env.production, com `bash` e `jq` de verdade (spec 002).

O bloco é extraído do `deploy.yml` (do início do passo até antes do `scp`) e roda com valores falsos.
Sem `jq` ou sem `bash` no PATH o teste é pulado; o CI (Ubuntu) tem os dois.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SENHA = "Abc$Segredo #123 xyz"


def _bloco():
    linhas = (RAIZ / ".github/workflows/deploy.yml").read_text(encoding="utf-8").splitlines()
    inicio = next(
        i for i, linha in enumerate(linhas) if "Generate .env.production on server" in linha
    )
    comeco = next(i for i in range(inicio, len(linhas)) if linhas[i].strip() == "run: |")
    fim = next(i for i in range(comeco, len(linhas)) if linhas[i].lstrip().startswith("scp -i"))
    corpo = [
        linha[10:] if linha.startswith(" " * 10) else linha.lstrip()
        for linha in linhas[comeco + 1 : fim]
    ]
    # o arquivo gerado vai para a pasta do teste, não para /tmp
    return "\n".join(corpo).replace("/tmp/.env.production", ".env.gerado")


def _executar(tmp_path, *, variables=None, segredos=None):
    bash, jq = shutil.which("bash"), shutil.which("jq")
    if bash is None or jq is None:
        pytest.skip("bash e jq são necessários")
    padrao = {
        "DJANGO_SECRET_KEY": "chave-do-django",
        "POSTGRES_PASSWORD": "senha-do-banco",
        "SENHA_ADMIN_INICIAL": SENHA,
    }
    resultado = subprocess.run(
        [bash, "-c", "set -eo pipefail\n" + _bloco()],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={
            **os.environ,
            **{**padrao, **(segredos or {})},
            "APP_NAME": "project-entrelinhas",
            "VARS_JSON": json.dumps(
                {
                    "ADMIN_USUARIO": "dono",
                    "ADMIN_EMAIL": "dono@example.com",
                    "DEPLOY_HOST": "h",
                    "DEPLOY_USER": "u",
                }
                | (variables or {})
            ),
        },
    )
    gerado = tmp_path / ".env.gerado"
    return resultado, gerado.read_text(encoding="utf-8") if gerado.exists() else ""


def test_ctl_8_bloco_real_grava_tudo_com_aspas_simples_e_sem_variaveis_de_infra(tmp_path):
    """[002] CTL-8: senha com `$`, `#` e espaço sai entre aspas simples, e DEPLOY_* não vai para o arquivo."""
    resultado, gerado = _executar(tmp_path)

    assert resultado.returncode == 0, resultado.stderr
    linhas = gerado.splitlines()
    assert "ADMIN_USUARIO='dono'" in linhas
    assert f"SENHA_ADMIN_INICIAL='{SENHA}'" in linhas
    assert "APP_NAME='project-entrelinhas'" in linhas
    assert all(linha.count("'") == 2 and linha.endswith("'") for linha in linhas), linhas
    assert not any(linha.startswith("DEPLOY_") for linha in linhas)


def test_ctl_9_variable_com_nome_de_segredo_derruba_o_passo(tmp_path):
    """[002] CTL-9: uma variable com o nome de um segredo é erro, e nada é gerado."""
    resultado, gerado = _executar(tmp_path, variables={"SENHA_ADMIN_INICIAL": "curta"})

    assert resultado.returncode != 0
    assert "variable com nome de segredo" in resultado.stderr
    assert gerado == ""


@pytest.mark.parametrize(
    ("variables", "mensagem"),
    [
        ({"ADMIN_EMAIL": "a'b@x.com"}, "aspa simples"),
        ({"ADMIN_EMAIL": "a@x.com\nADMIN_USUARIO=intruso"}, "quebra de linha"),
        ({"ADMIN_EMAIL": "a@x.com\r"}, "quebra de linha"),
    ],
)
def test_ctl_9_variable_com_aspa_ou_quebra_de_linha_derruba_o_passo(tmp_path, variables, mensagem):
    """[002] CTL-9: variable com aspa simples ou quebra de linha não vira linha extra nem comando."""
    resultado, gerado = _executar(tmp_path, variables=variables)

    assert resultado.returncode != 0
    assert mensagem in resultado.stderr
    assert "intruso" not in gerado


@pytest.mark.parametrize(
    ("segredos", "mensagem"),
    [
        ({"SENHA_ADMIN_INICIAL": ""}, "não configurado"),
        ({"SENHA_ADMIN_INICIAL": "abc\ndefghijkl"}, "quebra de linha"),
        ({"SENHA_ADMIN_INICIAL": "abc'defghijkl"}, "aspa simples"),
        ({"DJANGO_SECRET_KEY": ""}, "não configurado"),
    ],
)
def test_ctl_8_segredo_vazio_com_quebra_ou_aspa_derruba_o_passo(tmp_path, segredos, mensagem):
    """[002] CTL-8 / ABU-2: segredo inválido aborta antes de qualquer cópia para a VPS."""
    resultado, _ = _executar(tmp_path, segredos=segredos)

    assert resultado.returncode != 0
    assert mensagem in resultado.stderr


@pytest.mark.parametrize("senha_do_banco", ["com$cifrao", "com #cerquilha"])
def test_ctl_8_senha_do_banco_que_mudaria_com_as_aspas_derruba_o_passo(tmp_path, senha_do_banco):
    """[002] CTL-8: POSTGRES_PASSWORD que o Compose antigo mastigava não pode mudar de valor em silêncio."""
    resultado, gerado = _executar(tmp_path, segredos={"POSTGRES_PASSWORD": senha_do_banco})

    assert resultado.returncode != 0
    assert "POSTGRES_PASSWORD contém cifrão" in resultado.stderr
    assert "POSTGRES_PASSWORD" not in gerado


def test_ctl_8_chave_do_django_com_cifrao_e_aceita(tmp_path):
    """[002] CTL-8: DJANGO_SECRET_KEY com `$` só invalida sessões e passa."""
    resultado, gerado = _executar(tmp_path, segredos={"DJANGO_SECRET_KEY": "chave$com$cifrao"})

    assert resultado.returncode == 0, resultado.stderr
    assert "DJANGO_SECRET_KEY='chave$com$cifrao'" in gerado.splitlines()
