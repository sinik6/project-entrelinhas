"""[005] Regras sobre o código: um único ponto lê o texto, o log não leva conteúdo e o Admin não mostra registros."""

import logging
import re
from pathlib import Path

from django.contrib import admin

from apps.registros.models import Registro

from .conftest import arquivos_em, entregar

PASTA = Path(__file__).resolve().parents[1]
FONTES = [
    p
    for p in PASTA.rglob("*.py")
    if "tests" not in p.parts and "migrations" not in p.parts and p.name != "__init__.py"
]


def test_nfr_reg_1_so_o_dominio_le_o_texto_do_registro():
    """[005] NFR-REG-1 / CTL-31: nenhum outro arquivo do app acessa `.texto` nem `["texto"]`."""
    leituras = re.compile(r"\.texto\b|\[[\"']texto[\"']\]")
    suspeitos = [
        p.name
        for p in FONTES
        if p.name != "domain.py" and leituras.search(p.read_text(encoding="utf-8"))
    ]

    assert suspeitos == []
    assert any(p.name == "domain.py" for p in FONTES)


def test_nfr_reg_1_outros_apps_nao_leem_o_texto_do_registro():
    """[005] NFR-REG-1: fora de `registros`, quem precisar do texto usa a função de visibilidade (ver a 007)."""
    raiz = PASTA.parent
    leituras = re.compile(r"registro\w*\.texto\b|Registro\.objects[^\n]*texto")
    for arquivo in raiz.rglob("*.py"):
        if (
            "tests" in arquivo.parts
            or "migrations" in arquivo.parts
            or "registros" in arquivo.parts
        ):
            continue
        assert not leituras.search(arquivo.read_text(encoding="utf-8")), arquivo


def test_nfr_reg_1_consultas_ao_registro_nao_trazem_a_coluna_texto_em_nenhum_arquivo():
    """[005] NFR-REG-1 (reforço da auditoria): `Registro.objects` seguido de `values`, `values_list` ou `only`
    com `texto` nas linhas seguintes (a consulta pode quebrar em várias linhas) também é leitura do texto."""
    raiz = PASTA.parent
    for arquivo in raiz.rglob("*.py"):
        if "tests" in arquivo.parts or "migrations" in arquivo.parts or arquivo.name == "domain.py":
            continue
        linhas = arquivo.read_text(encoding="utf-8").splitlines()
        for i, linha in enumerate(linhas):
            if "Registro.objects" not in linha:
                continue
            janela = " ".join(linhas[i : i + 6])
            if ".create(" in janela.split("Registro.objects", 1)[1][:30]:
                continue  # escrever o texto na entrega não é ler
            assert not re.search(r"\.(values|values_list|only|defer)\([^)]*texto", janela), (
                arquivo,
                i + 1,
            )


def test_nfr_reg_3_log_da_entrega_nao_leva_texto_trecho_nem_foto(dono, caplog, pasta_de_fotos):
    """[005] NFR-REG-3 / CTL-37: só ids e contagens."""
    texto = "SEGREDO-DO-DIARIO-QUE-NAO-PODE-IR-AO-LOG"
    with caplog.at_level(logging.DEBUG):
        resposta = entregar(
            dono, texto=texto, visibilidade="partial", trecho={"inicio": 0, "fim": 10}
        )

    assert resposta.status_code == 201
    registrado = "\n".join(r.getMessage() for r in caplog.records)
    assert "SEGREDO" not in registrado
    assert "foto.jpg" not in registrado, "o nome enviado da foto não vai ao log"
    assert not any(p.name in registrado for p in arquivos_em(pasta_de_fotos)), (
        "o nome do arquivo guardado também não"
    )
    assert resposta.json()["id"] in registrado, "o registro tem que deixar rastro (id)"


def test_nfr_reg_3_erro_de_validacao_nao_repete_o_texto_nem_no_log(dono, caplog):
    """[005] NFR-REG-3 / CTL-37."""
    with caplog.at_level(logging.DEBUG):
        resposta = entregar(dono, texto="SEGREDO\x00curto")

    assert resposta.status_code == 422
    assert "SEGREDO" not in resposta.content.decode()
    assert "SEGREDO" not in "\n".join(r.getMessage() for r in caplog.records)


def test_nfr_reg_4_admin_nao_registra_registro_nem_foto():
    """[005] NFR-REG-4 / CTL-37 / CTL-39: o Django Admin não mostra o texto dos registros."""
    from apps.fotos.models import Foto

    assert Registro not in admin.site._registry
    assert Foto not in admin.site._registry
