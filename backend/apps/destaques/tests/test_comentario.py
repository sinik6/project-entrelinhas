"""[007] Comentar, editar, apagar, limites (com threads reais) e autoria."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import connections

from apps.destaques.models import Comentario, Destaque

from .conftest import Cliente, apagar, comentar, destacar, listar, registro_de

EMAILS = ("dono@example.com", "par@example.com")


def _destaque(par, **kw):
    dono, parceiro = par
    registro = registro_de(dono)
    return registro, destacar(parceiro, registro, 0, 7, **kw).json()["id"]


def test_req_14_1_membro_comenta_com_autor_e_hora(par):
    """[007] REQ-14.1."""
    dono, _ = par
    _, d = _destaque(par)

    resposta = comentar(dono, d, "Eu também gostei.")

    assert resposta.status_code == 201, resposta.content
    c = resposta.json()
    assert c["texto"] == "Eu também gostei."
    assert c["autor"]["nome"] == "Dono"
    assert c["meu"] is True
    assert c["criado_em"] and c["editado_em"] is None


def test_req_14_1_texto_invalido_da_422_sem_eco(par):
    """[007] REQ-14.1: vazio, só espaços, 1001 caracteres, controle, tipo errado; sem repetir o texto."""
    dono, _ = par
    _, d = _destaque(par)

    for texto in ("", "   \n", "x" * 1001, "ruim\x00ruim", "ruim\x1bruim", 5, None, ["a"]):
        resposta = dono.postar(f"/api/v1/destaques/{d}/comentarios", {"texto": texto})
        assert resposta.status_code == 422, repr(texto)
        assert "ruim" not in resposta.content.decode()
    assert comentar(dono, d, "x" * 1000).status_code == 201
    assert comentar(dono, d, "linha um\nlinha\tdois").status_code == 201


def test_req_14_2_vigesimo_primeiro_comentario_da_409(par):
    """[007] REQ-14.2."""
    dono, parceiro = par
    _, d = _destaque(par)
    for i in range(20):
        assert comentar(dono if i % 2 else parceiro, d, f"comentário {i}").status_code == 201

    resposta = comentar(dono, d, "um a mais")

    assert resposta.status_code == 409
    assert Comentario.objects.filter(destaque_id=d).count() == 20


@pytest.mark.django_db(transaction=True)
def test_abu_15_vinte_comentarios_simultaneos_nao_passam_do_limite(par):
    """[007] ABU-15: 25 pedidos ao mesmo tempo, no máximo 20 entram (threads reais)."""
    _, d = _destaque(par)
    largada = threading.Barrier(25)

    def tentar(i):
        try:
            cliente = Cliente()
            assert cliente.entrar(EMAILS[i % 2]).status_code == 200
            largada.wait(timeout=30)
            return comentar(cliente, d, f"c{i}").status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=25) as pool:
        codigos = list(pool.map(tentar, range(25)))

    assert codigos.count(201) == 20, codigos
    assert codigos.count(409) == 5
    assert Comentario.objects.filter(destaque_id=d).count() == 20


def test_req_13_5_qinquagesimo_primeiro_destaque_da_409_e_vale_por_pessoa(par):
    """[007] REQ-13.5: o limite é de 50 por pessoa por registro; a outra pessoa tem os seus."""
    dono, parceiro = par
    registro = registro_de(dono)
    for i in range(50):
        assert destacar(parceiro, registro, 0, 5).status_code == 201, i

    assert destacar(parceiro, registro, 0, 5).status_code == 409
    assert destacar(dono, registro, 0, 5).status_code == 201
    assert Destaque.objects.filter(registro_id=registro).count() == 51


@pytest.mark.django_db(transaction=True)
def test_abu_15_destaques_simultaneos_nao_passam_de_50(par):
    """[007] ABU-15 / REQ-13.5: 60 pedidos juntos, 50 entram."""
    dono, _ = par
    registro = registro_de(dono)
    largada = threading.Barrier(60)

    def tentar(_):
        try:
            cliente = Cliente()
            assert cliente.entrar(EMAILS[1]).status_code == 200
            largada.wait(timeout=30)
            return destacar(cliente, registro, 0, 5).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=60) as pool:
        codigos = list(pool.map(tentar, range(60)))

    assert codigos.count(201) == 50, codigos
    assert Destaque.objects.filter(registro_id=registro).count() == 50


def test_req_13_6_apagar_o_destaque_apaga_os_comentarios_dele(par):
    """[007] REQ-13.6."""
    dono, parceiro = par
    _, d = _destaque(par, comentario="primeiro")
    comentar(dono, d, "resposta do dono")

    resposta = apagar(parceiro, f"/api/v1/destaques/{d}")

    assert resposta.status_code == 204
    assert Destaque.objects.count() == 0
    assert Comentario.objects.count() == 0


def test_req_13_7_so_quem_criou_apaga_o_destaque(par):
    """[007] REQ-13.7: 403 e nada muda."""
    dono, _ = par
    _, d = _destaque(par, comentario="meu")

    resposta = apagar(dono, f"/api/v1/destaques/{d}")

    assert resposta.status_code == 403
    assert resposta.json() == {"detalhe": "Só quem escreveu pode fazer isso."}
    assert Destaque.objects.count() == 1 and Comentario.objects.count() == 1


def test_req_14_3_autor_edita_o_comentario_e_a_hora_da_edicao_aparece(par):
    """[007] REQ-14.3."""
    dono, _ = par
    _, d = _destaque(par)
    c = comentar(dono, d, "antes").json()["id"]

    resposta = dono.alterar(f"/api/v1/comentarios/{c}", {"texto": "depois"})

    assert resposta.status_code == 200
    assert resposta.json()["texto"] == "depois"
    assert resposta.json()["editado_em"] is not None


def test_req_14_3_edicao_invalida_da_422_e_nao_muda(par):
    """[007] REQ-14.3 / REQ-14.1."""
    dono, _ = par
    _, d = _destaque(par)
    c = comentar(dono, d, "intacto").json()["id"]

    assert dono.alterar(f"/api/v1/comentarios/{c}", {"texto": " "}).status_code == 422
    assert Comentario.objects.get(pk=c).texto == "intacto"


def test_abu_16_ninguem_edita_nem_apaga_o_comentario_do_outro(par):
    """[007] ABU-16 / REQ-14.3: 403 e nada muda."""
    dono, parceiro = par
    _, d = _destaque(par)
    c = comentar(dono, d, "do dono").json()["id"]

    editar = parceiro.alterar(f"/api/v1/comentarios/{c}", {"texto": "invadido"})
    remover = apagar(parceiro, f"/api/v1/comentarios/{c}")

    assert (editar.status_code, remover.status_code) == (403, 403)
    assert Comentario.objects.get(pk=c).texto == "do dono"
    assert Comentario.objects.get(pk=c).editado_em is None


def test_req_14_4_autor_apaga_o_proprio_comentario(par):
    """[007] REQ-14.4."""
    dono, _ = par
    _, d = _destaque(par)
    c = comentar(dono, d, "some").json()["id"]

    assert apagar(dono, f"/api/v1/comentarios/{c}").status_code == 204
    assert Comentario.objects.count() == 0
    assert Destaque.objects.count() == 1


def test_req_14_6_outro_grupo_recebe_404_em_tudo(par, estranho):
    """[007] REQ-14.6 / ABU-16: registro, destaque e comentário de outro grupo."""
    registro, d = _destaque(par, comentario="algo")
    c = Comentario.objects.get().pk

    respostas = [
        listar(estranho, registro),
        destacar(estranho, registro, 0, 5),
        comentar(estranho, d, "intruso"),
        apagar(estranho, f"/api/v1/destaques/{d}"),
        estranho.alterar(f"/api/v1/comentarios/{c}", {"texto": "intruso"}),
        apagar(estranho, f"/api/v1/comentarios/{c}"),
    ]

    assert [r.status_code for r in respostas] == [404] * 6
    assert Comentario.objects.count() == 1


def test_req_14_6_ids_malformados_ou_inexistentes_dao_404(par):
    """[007] REQ-14.6."""
    dono, _ = par
    for url in (
        "/api/v1/registros/xx/destaques",
        "/api/v1/registros/00000000-0000-0000-0000-000000000000/destaques",
    ):
        assert dono.get(url).status_code == 404
    assert apagar(dono, "/api/v1/destaques/xx").status_code == 404
    assert comentar(dono, "00000000-0000-0000-0000-000000000000", "x").status_code == 404
    assert dono.alterar("/api/v1/comentarios/xx", {"texto": "x"}).status_code == 404
    assert apagar(dono, "/api/v1/comentarios/xx").status_code == 404
