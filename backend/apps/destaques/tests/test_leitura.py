"""[007] Leitura por registro, isolamento, log, Admin e a única porta ao texto."""

import logging
import re
from pathlib import Path

from django.contrib import admin

from apps.destaques.models import Comentario, Destaque

from .conftest import comentar, destacar, listar, registro_de

PASTA = Path(__file__).resolve().parents[1]


def test_req_14_5_lista_com_posicao_trecho_autor_cor_comentarios_e_meu(par):
    """[007] REQ-14.5: cada destaque com tudo; `meu` depende de quem pede."""
    dono, parceiro = par
    registro = registro_de(dono)
    d = destacar(parceiro, registro, 0, 7, comentario="da Bia").json()["id"]
    comentar(dono, d, "do dono")
    destacar(dono, registro, 8, 14)

    da_bia = listar(parceiro, registro).json()
    do_dono = listar(dono, registro).json()

    assert len(da_bia) == 2 == len(do_dono)
    primeiro = next(x for x in da_bia if x["id"] == d)
    assert primeiro["trecho"] == "Primeir"
    assert primeiro["meu"] is True and primeiro["autor"] == {"nome": "Bia", "cor": "#B45309"}
    assert [(c["texto"], c["meu"], c["autor"]["nome"]) for c in primeiro["comentarios"]] == [
        ("da Bia", True, "Bia"),
        ("do dono", False, "Dono"),
    ]
    assert next(x for x in do_dono if x["id"] == d)["meu"] is False
    assert all(
        set(x) >= {"id", "inicio", "fim", "trecho", "autor", "meu", "criado_em"} for x in da_bia
    )


def test_req_14_5_a_lista_vem_em_ordem_de_criacao_e_a_cor_e_a_de_agora(par):
    """[007] REQ-14.5 / suposição: a cor é a do perfil lido na hora."""
    from apps.acesso.models import Perfil

    dono, parceiro = par
    registro = registro_de(dono)
    destacar(parceiro, registro, 0, 3)
    destacar(parceiro, registro, 4, 8)
    Perfil.objects.filter(nome="Bia").update(cor="#0E7490")

    lista = listar(dono, registro).json()

    assert [x["inicio"] for x in lista] == [0, 4]
    assert {x["autor"]["cor"] for x in lista} == {"#0E7490"}


def test_req_14_6_sem_sessao_da_401_e_registro_de_outro_grupo_da_404(par, estranho, cliente):
    """[007] REQ-14.6 / CTL-52."""
    dono, _ = par
    registro = registro_de(dono)

    assert cliente.get(f"/api/v1/registros/{registro}/destaques").status_code in (401, 403)
    assert listar(estranho, registro).status_code == 404


def test_req_14_6_quem_saiu_do_grupo_nao_le_destaques_do_grupo_antigo(par, novo_grupo):
    """[007] REQ-14.6 + REQ-9.8 da 005: a regra de leitura do registro vale para os destaques."""
    from apps.acesso.models import Perfil

    dono, parceiro = par
    registro = registro_de(dono)
    destacar(dono, registro, 0, 5)
    Perfil.objects.filter(nome="Bia").update(grupo=novo_grupo())

    assert listar(parceiro, registro).status_code == 404
    assert listar(dono, registro).status_code == 200


def test_nfr_dest_2_admin_nao_mostra_destaques_nem_comentarios():
    """[007] NFR-DEST-2 / CTL-55."""
    assert Destaque not in admin.site._registry
    assert Comentario not in admin.site._registry


def test_nfr_dest_log_nao_leva_comentario_nem_trecho_nem_erro_com_eco(par, caplog):
    """[007] REQ-14.7 / CTL-55: só ids e contagens."""
    dono, parceiro = par
    registro = registro_de(dono, texto="TRECHO-SECRETO-NO-LOG e mais algum texto")
    with caplog.at_level(logging.DEBUG):
        d = destacar(parceiro, registro, 0, 20, comentario="COMENTARIO-SECRETO-NO-LOG").json()
        comentar(dono, d["id"], "OUTRO-COMENTARIO-SECRETO")
        destacar(parceiro, registro, 0, 9999)
        parceiro.alterar(
            f"/api/v1/comentarios/{d['comentarios'][0]['id']}", {"texto": "EDICAO-SECRETA"}
        )

    registrado = "\n".join(r.getMessage() for r in caplog.records)
    for segredo in ("SECRETO", "EDICAO"):
        assert segredo not in registrado
    assert d["id"] in registrado, "o destaque precisa deixar rastro (id)"


def test_nfr_dest_so_o_dominio_da_005_le_o_texto_do_registro():
    """[007] CTL-56: este app usa `texto_visivel_para`; nada de `Registro.texto` aqui."""
    for arquivo in PASTA.glob("*.py"):
        codigo = arquivo.read_text(encoding="utf-8")
        assert not re.search(r"registro\w*\.texto\b", codigo), arquivo
        assert not re.search(r"Registro\.objects[^\n]*texto", codigo), arquivo
    assert "texto_visivel_para" in (PASTA / "services.py").read_text(encoding="utf-8")
