"""[005] Entrega do registro: fotos, texto, trecho, um por dia (com threads reais), sem grupo, imutabilidade."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import connections

from apps.fotos.models import Foto
from apps.registros.models import Registro

from .conftest import (
    TEXTO_BASE,
    VERDE,
    Cliente,
    entregar,
    enviar_foto,
    foto_manuscrito,
    imagem_bytes,
)


def test_req_8_1_entrega_cria_o_registro_anexa_as_fotos_e_registra_a_hora_do_servidor(
    dono, relogio
):
    """[005] REQ-8.1: 201, registro do grupo, fotos anexadas em ordem, hora do servidor."""
    relogio.fixar(2026, 11, 5, 15, 0)
    fotos = [foto_manuscrito(dono), foto_manuscrito(dono)]

    resposta = entregar(dono, fotos=fotos)

    assert resposta.status_code == 201, resposta.content
    corpo = resposta.json()
    assert corpo["meu"] is True
    assert corpo["texto"] == TEXTO_BASE
    assert corpo["visibilidade"] == "full"
    assert corpo["fotos"] == fotos
    registro = Registro.objects.get()
    assert registro.entregue_em.isoformat().startswith("2026-11-05T15:00:00")
    assert registro.data.isoformat() == "2026-11-05"
    assert registro.grupo_id == registro.autor.perfil.grupo_id
    assert Foto.objects.filter(registro=registro, anexada=True).count() == 2
    assert [str(f.id) for f in Foto.objects.filter(registro=registro).order_by("ordem")] == fotos


def test_req_8_1_o_cliente_nao_escolhe_a_hora_nem_o_dia(dono, relogio):
    """[005] REQ-8.1: campos extras como `entregue_em` e `data` são ignorados."""
    relogio.fixar(2026, 11, 5, 15, 0)
    foto = foto_manuscrito(dono)

    resposta = dono.postar(
        "/api/v1/registros",
        {
            "texto": TEXTO_BASE,
            "visibilidade": "full",
            "fotos": [foto],
            "entregue_em": "2020-01-01T00:00:00Z",
            "data": "2020-01-01",
            "autor": 99,
        },
    )

    assert resposta.status_code == 201
    assert Registro.objects.get().data.isoformat() == "2026-11-05"


@pytest.mark.parametrize("visibilidade", ["full", "private", "partial"])
def test_req_8_1_as_tres_visibilidades_sao_aceitas(dono, visibilidade):
    """[005] REQ-8.1: full, private e partial entregam."""
    trecho = {"inicio": 0, "fim": 5} if visibilidade == "partial" else None

    resposta = entregar(dono, visibilidade=visibilidade, trecho=trecho)

    assert resposta.status_code == 201, resposta.content
    assert resposta.json()["visibilidade"] == visibilidade


def test_req_8_2_sem_foto_nao_entrega(dono):
    """[005] REQ-8.2: entrega só vale com foto."""
    resposta = dono.postar(
        "/api/v1/registros", {"texto": TEXTO_BASE, "visibilidade": "full", "fotos": []}
    )

    assert resposta.status_code == 422
    assert "fotos" in resposta.json()["campos"]
    assert Registro.objects.count() == 0


def test_req_8_2_mais_de_3_fotos_nao_entrega(dono):
    """[005] REQ-8.2: o teto é 3."""
    fotos = [foto_manuscrito(dono) for _ in range(4)]

    resposta = entregar(dono, fotos=fotos)

    assert resposta.status_code == 422
    assert Registro.objects.count() == 0
    assert Foto.objects.filter(anexada=True).count() == 0


def test_req_8_2_tres_fotos_e_o_limite_aceito(dono):
    """[005] REQ-8.2: exatamente 3 entrega."""
    assert entregar(dono, n_fotos=3).status_code == 201


def test_req_8_2_foto_de_outra_pessoa_inexistente_ou_malformada_tem_a_mesma_recusa(dono, parceiro):
    """[005] REQ-8.2 / CTL-36: a resposta não diz se a foto existe nem de quem é."""
    alheia = foto_manuscrito(parceiro())
    respostas = [
        entregar(dono, fotos=[alheia]),
        entregar(dono, fotos=["00000000-0000-4000-8000-000000000000"]),
        entregar(dono, fotos=["isto-nao-e-uuid"]),
        entregar(dono, fotos=[123]),
    ]

    assert {r.status_code for r in respostas} == {422}
    assert len({str(r.json()) for r in respostas}) == 1
    assert Registro.objects.count() == 0
    assert Foto.objects.get(pk=alheia).anexada is False


def test_req_8_2_foto_de_perfil_ou_repetida_nao_serve(dono):
    """[005] REQ-8.2: só avulsa de manuscrito do próprio autor, sem repetir."""
    perfil = enviar_foto(dono, imagem_bytes(), finalidade="perfil").json()["id"]
    boa = foto_manuscrito(dono)

    assert entregar(dono, fotos=[perfil]).status_code == 422
    assert entregar(dono, fotos=[boa, boa]).status_code == 422
    assert entregar(dono, fotos=[boa]).status_code == 201


def test_req_8_2_foto_ja_usada_em_outro_registro_nao_serve(dono, relogio):
    """[005] REQ-8.2: a foto anexada ontem não pode ser anexada hoje."""
    relogio.fixar(2026, 11, 5)
    foto = foto_manuscrito(dono)
    assert entregar(dono, fotos=[foto]).status_code == 201
    relogio.fixar(2026, 11, 6)

    resposta = entregar(dono, fotos=[foto])

    assert resposta.status_code == 422


def test_req_8_3_texto_curto_longo_ou_com_controle_e_recusado_e_nada_e_anexado(dono):
    """[005] REQ-8.3 / NFR-REG-2: 422 por API, e as fotos continuam avulsas."""
    foto = foto_manuscrito(dono)
    for texto in ("curto", "a" * 20001, "a" * 10 + "\x00", "a" * 10 + "\r"):
        resposta = entregar(dono, texto=texto, fotos=[foto])

        assert resposta.status_code == 422, texto[:12]
        assert "texto" in resposta.json()["campos"]
        assert "a" * 10 not in str(resposta.json())
    assert Registro.objects.count() == 0
    assert Foto.objects.get(pk=foto).anexada is False


def test_req_8_3_dez_caracteres_uteis_e_vinte_mil_sao_aceitos(dono, relogio):
    """[005] REQ-8.3: os limites são inclusivos."""
    relogio.fixar(2026, 11, 5)
    assert entregar(dono, texto="a" * 10).status_code == 201
    relogio.fixar(2026, 11, 6)
    assert entregar(dono, texto="b" * 20000).status_code == 201


def test_req_8_4_partial_exige_trecho_valido_e_full_private_recusam_trecho(dono):
    """[005] REQ-8.4 / ABU-11: 422 em todos os casos ruins, nunca 500."""
    foto = foto_manuscrito(dono)
    ruins = [
        ("partial", None),
        ("partial", {"inicio": 5, "fim": 5}),
        ("partial", {"inicio": 6, "fim": 2}),
        ("partial", {"inicio": -1, "fim": 3}),
        ("partial", {"inicio": 0, "fim": len(TEXTO_BASE) + 1}),
        ("partial", {"inicio": "0", "fim": 3}),
        ("partial", {"inicio": 0.5, "fim": 3}),
        ("partial", {"inicio": True, "fim": 3}),
        ("partial", {"inicio": None, "fim": 3}),
        ("partial", {"inicio": 0}),
        ("partial", "0-5"),
        ("full", {"inicio": 0, "fim": 5}),
        ("private", {"inicio": 0, "fim": 5}),
        ("secreto", None),
    ]
    for visibilidade, trecho in ruins:
        resposta = entregar(dono, visibilidade=visibilidade, trecho=trecho, fotos=[foto])

        assert resposta.status_code == 422, (visibilidade, trecho, resposta.content)
    assert Registro.objects.count() == 0


def test_req_8_4_trecho_em_emoji_conta_pontos_de_codigo(dono):
    """[005] REQ-8.4 / ADR-0009: o fim máximo é o número de pontos de código, não de unidades UTF-16."""
    texto = "😀" * 10 + "fim do texto"
    assert len(texto) == 22 and len(texto.encode("utf-16-le")) // 2 == 32

    ok = entregar(dono, texto=texto, visibilidade="partial", trecho={"inicio": 0, "fim": 22})

    assert ok.status_code == 201, ok.content


def test_req_8_5_dois_registros_no_mesmo_dia_o_segundo_e_409(dono, relogio):
    """[005] REQ-8.5: um por pessoa por dia."""
    relogio.fixar(2026, 11, 5, 10)
    assert entregar(dono).status_code == 201
    relogio.fixar(2026, 11, 5, 22)

    segundo = entregar(dono)

    assert segundo.status_code == 409
    assert segundo.json() == {"detalhe": "Você já entregou o registro de hoje."}
    assert Registro.objects.count() == 1


def test_req_8_5_o_dia_vira_a_meia_noite_de_sao_paulo_e_nao_a_do_utc(dono, relogio):
    """[005] REQ-8.5 / ABU-9: 23h30 e 00h30 de São Paulo são dias diferentes; 21h e 23h30 de SP são o mesmo."""
    relogio.fixar(2026, 11, 6, 2, 30)  # 23h30 de 05/11 em São Paulo (UTC-3)
    assert entregar(dono).status_code == 201
    relogio.fixar(2026, 11, 6, 3, 30)  # 00h30 de 06/11 em São Paulo
    assert entregar(dono).status_code == 201
    relogio.fixar(2026, 11, 6, 23, 30)  # 20h30 de 06/11 em São Paulo: já entregou o dia 06
    assert entregar(dono).status_code == 409

    assert sorted(r.data.isoformat() for r in Registro.objects.all()) == [
        "2026-11-05",
        "2026-11-06",
    ]


def test_req_8_5_cada_pessoa_tem_o_seu_registro_do_dia(dono, parceiro, relogio):
    """[005] REQ-8.5: o limite é por pessoa."""
    relogio.fixar(2026, 11, 5)
    bia = parceiro()

    assert entregar(dono).status_code == 201
    assert entregar(bia).status_code == 201


@pytest.mark.django_db(transaction=True)
def test_abu_9_pedidos_simultaneos_do_mesmo_dia_criam_um_so_registro(
    novo_participante, logar, relogio
):
    """[005] ABU-9 / REQ-8.5: 6 threads entregando ao mesmo tempo; um 201 e o resto 409."""
    novo_participante("dono@example.com", nome="Dono", cor=VERDE)
    dono = logar("dono@example.com")
    assert dono.postar("/api/v1/grupo").status_code == 201
    relogio.fixar(2026, 11, 5)
    fotos = [foto_manuscrito(dono) for _ in range(6)]
    largada = threading.Barrier(6)

    def tentar(foto):
        try:
            cliente = Cliente()
            assert cliente.entrar("dono@example.com").status_code == 200
            largada.wait(timeout=20)
            return cliente.postar(
                "/api/v1/registros", {"texto": TEXTO_BASE, "visibilidade": "full", "fotos": [foto]}
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=6) as pool:
        resultados = sorted(pool.map(tentar, fotos))

    assert resultados == [201, 409, 409, 409, 409, 409], resultados
    assert Registro.objects.count() == 1
    assert Foto.objects.filter(anexada=True).count() == 1


def test_req_8_6_sem_grupo_nao_entrega(novo_participante, logar):
    """[005] REQ-8.6: participante com perfil e sem grupo recebe 409; sem perfil também."""
    novo_participante("solo@example.com", nome="Solo")
    novo_participante("adm@example.com", nome=None)
    for email in ("solo@example.com", "adm@example.com"):
        cliente = logar(email)
        foto = foto_manuscrito(cliente)

        resposta = entregar(cliente, fotos=[foto])

        assert resposta.status_code == 409, email
        assert resposta.json() == {"detalhe": "Entre em um grupo antes de escrever."}
    assert Registro.objects.count() == 0


def test_req_8_7_registro_entregue_nao_se_edita_nao_se_apaga_nem_muda_de_visibilidade(dono):
    """[005] REQ-8.7: PUT, PATCH e DELETE em /registros/{id} respondem 405."""
    registro_id = entregar(dono).json()["id"]
    url = f"/api/v1/registros/{registro_id}"
    token = dono.token()

    for metodo in (dono.put, dono.patch, dono.delete):
        resposta = metodo(url, {"visibilidade": "private"}, format="json", HTTP_X_CSRFTOKEN=token)

        assert resposta.status_code == 405, metodo
    assert Registro.objects.get().visibilidade == "full"


def test_req_8_7_a_lista_tambem_nao_aceita_alteracao_em_massa(dono):
    """[005] REQ-8.7: /registros só aceita GET e POST."""
    assert dono.delete("/api/v1/registros", HTTP_X_CSRFTOKEN=dono.token()).status_code == 405


def test_req_8_1_anonimo_recebe_401(dono, cliente):
    """[005] REQ-1.4 estendido: sem sessão nenhuma rota de registro responde."""
    assert cliente.get("/api/v1/registros?mes=2026-11").status_code == 401
    assert cliente.get("/api/v1/registros/00000000-0000-4000-8000-000000000000").status_code == 401
    assert cliente.post("/api/v1/registros", {}, format="json").status_code in (401, 403)


def test_req_8_1_entrega_atomica_foto_invalida_nao_deixa_registro_pela_metade(dono):
    """[005] REQ-8.1: se algo falha, nada é criado nem anexado."""
    boa = foto_manuscrito(dono)

    resposta = entregar(dono, fotos=[boa, "00000000-0000-4000-8000-000000000000"])

    assert resposta.status_code == 422
    assert Registro.objects.count() == 0
    assert Foto.objects.get(pk=boa).anexada is False


def test_req_8_2_foto_marcada_como_anexada_nao_serve_mesmo_sem_registro(dono):
    """[005] REQ-8.2: `anexada` conta por si (a foto pode estar em uso por outro caminho)."""
    foto = foto_manuscrito(dono)
    Foto.objects.filter(pk=foto).update(anexada=True)

    assert entregar(dono, fotos=[foto]).status_code == 422
    assert Registro.objects.count() == 0
