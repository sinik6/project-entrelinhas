"""[003] Convite por link de uso único (US-3): geração, aceite, respostas iguais, grupo cheio e concorrência."""

import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from django.utils import timezone

from apps.acesso.models import Convite, Grupo, Perfil
from apps.acesso.tests.conftest import AMBAR, OUTRA_SENHA, ROXO, VERDE, Cliente

FALHA = {"detalhe": "Não foi possível usar este convite."}


def gerar(dono):
    resposta = dono.postar("/api/v1/grupo/convites")
    assert resposta.status_code == 201, resposta.content
    return resposta.json()["codigo"]


def dados_de_bia(codigo, **trocas):
    return {
        "codigo": codigo,
        "nome": "Bia",
        "email": "bia@example.com",
        "senha": OUTRA_SENHA,
        "cor": AMBAR,
    } | trocas


def aceitar(codigo, **trocas):
    cliente = Cliente()
    return cliente, cliente.postar("/api/v1/convites/aceitar", dados_de_bia(codigo, **trocas))


def test_req_3_1_gera_convite(grupo_do_dono):
    """[003] REQ-3.1: o membro de um grupo com vaga recebe o código e a validade."""
    resposta = grupo_do_dono.postar("/api/v1/grupo/convites")

    assert resposta.status_code == 201
    assert set(resposta.json()) == {"codigo", "expira_em"}
    assert Convite.objects.count() == 1


def test_req_3_1_sem_grupo_nao_gera_convite(novo_participante, logar):
    """[003] REQ-3.1: quem não tem grupo não gera convite."""
    novo_participante("ana@example.com")

    assert logar("ana@example.com").postar("/api/v1/grupo/convites").status_code == 409


def test_req_3_3_convite_vale_7_dias(grupo_do_dono):
    """[003] REQ-3.3: a validade é de 7 dias a partir da criação."""
    antes = timezone.now()
    gerar(grupo_do_dono)

    convite = Convite.objects.get()
    assert (
        timedelta(days=7) - timedelta(minutes=1)
        <= convite.expira_em - antes
        <= timedelta(days=7, minutes=1)
    )


def test_req_3_3_convite_expirado_e_recusado(grupo_do_dono):
    """[003] REQ-3.3: passados os 7 dias, o convite é recusado como qualquer outro inválido."""
    codigo = gerar(grupo_do_dono)
    Convite.objects.update(expira_em=timezone.now() - timedelta(seconds=1))

    _, resposta = aceitar(codigo)

    assert resposta.status_code == 400
    assert resposta.json() == FALHA
    assert not get_user_model().objects.filter(email="bia@example.com").exists()


def test_req_3_2_novo_convite_invalida_o_anterior(grupo_do_dono):
    """[003] REQ-3.2: só um convite pendente por grupo; o anterior deixa de valer."""
    primeiro = gerar(grupo_do_dono)
    segundo = gerar(grupo_do_dono)

    _, com_o_primeiro = aceitar(primeiro)
    _, com_o_segundo = aceitar(segundo)

    assert com_o_primeiro.status_code == 400
    assert com_o_segundo.status_code == 201
    assert Convite.objects.filter(invalidado_em__isnull=False).count() == 1


def test_req_3_4_aceitar_cria_conta_perfil_e_entrada(grupo_do_dono):
    """[003] REQ-3.4: o aceite cria a conta (login = e-mail), o perfil e a entrada no grupo, e já inicia a sessão."""
    codigo = gerar(grupo_do_dono)

    bia, resposta = aceitar(codigo)

    assert resposta.status_code == 201
    assert resposta.json()["email"] == "bia@example.com"
    assert resposta.json()["completo"] is True
    usuario = get_user_model().objects.get(email="bia@example.com")
    assert usuario.username == "bia@example.com"
    assert usuario.check_password(OUTRA_SENHA)
    assert not usuario.is_staff and not usuario.is_superuser
    perfil = Perfil.objects.get(usuario=usuario)
    assert (perfil.nome, perfil.cor) == ("Bia", AMBAR)
    assert perfil.grupo == Perfil.objects.get(usuario__email="dono@example.com").grupo
    assert Convite.objects.get().usado_em is not None
    sessao = bia.get("/api/v1/perfil")
    assert sessao.status_code == 200
    assert [m["nome"] for m in sessao.json()["grupo"]["membros"]] == ["Dono", "Bia"]
    assert sessao.json()["grupo"]["vaga"] is False


def test_req_3_4_dados_invalidos_recusados_e_o_convite_continua_valendo(grupo_do_dono):
    """[003] REQ-3.4 / NFR-SEC-3: senha fraca, cor ilegível, cor igual à do dono, nome vazio e e-mail inválido dão 422."""
    codigo = gerar(grupo_do_dono)

    casos = {
        "senha": aceitar(codigo, senha="curta1!")[1],
        "cor": aceitar(codigo, cor="#FFFFFF")[1],
        "cor igual": aceitar(codigo, cor=VERDE)[1],
        "nome": aceitar(codigo, nome="   ")[1],
        "email": aceitar(codigo, email="sem-arroba")[1],
    }

    for campo, resposta in casos.items():
        assert resposta.status_code == 422, campo
    assert set(casos["senha"].json()["campos"]) == {"senha"}
    assert set(casos["cor"].json()["campos"]) == {"cor"}
    assert set(casos["cor igual"].json()["campos"]) == {"cor"}
    assert set(casos["nome"].json()["campos"]) == {"nome"}
    assert set(casos["email"].json()["campos"]) == {"email"}
    assert Convite.objects.get().usado_em is None
    assert aceitar(codigo)[1].status_code == 201


def test_req_3_5_convite_usado_expirado_ou_inexistente_respondem_igual(grupo_do_dono):
    """[003] REQ-3.5: usado, expirado e inexistente dão o mesmo status e o mesmo corpo."""
    usado = gerar(grupo_do_dono)
    assert aceitar(usado)[1].status_code == 201
    novo = convite_pendente_a_forca()
    expirado = novo
    Convite.objects.filter(usado_em__isnull=True).update(
        expira_em=timezone.now() - timedelta(seconds=1)
    )

    respostas = [
        aceitar(usado, email="outra@example.com")[1],
        aceitar(expirado, email="outra@example.com")[1],
        aceitar("codigo-que-nunca-existiu", email="outra@example.com")[1],
        aceitar("", email="outra@example.com")[1],
    ]

    assert {(r.status_code, r.content) for r in respostas} == {(400, respostas[0].content)}
    assert respostas[0].json() == FALHA


def convite_pendente_a_forca():
    """Cria à mão um convite pendente já vencido: o grupo está cheio e a API não gera mais convites."""
    grupo = Grupo.objects.get()
    dono = Perfil.objects.get(usuario__email="dono@example.com")
    codigo = "convite-de-teste-vencido"
    Convite.objects.create(
        grupo=grupo,
        criado_por=dono,
        codigo_hash=hashlib.sha256(codigo.encode()).hexdigest(),
        expira_em=timezone.now() + timedelta(days=1),
    )
    return codigo


def test_req_3_6_email_ja_usado_responde_igual(grupo_do_dono):
    """[003] REQ-3.6: aceitar com um e-mail que já tem conta dá a mesma resposta de convite inválido."""
    codigo = gerar(grupo_do_dono)

    _, com_email_existente = aceitar(codigo, email="DONO@example.com")
    _, convite_invalido = aceitar("codigo-inexistente")

    assert (com_email_existente.status_code, com_email_existente.json()) == (400, FALHA)
    assert (convite_invalido.status_code, convite_invalido.json()) == (400, FALHA)
    assert Convite.objects.get().usado_em is None


def test_abu_2_aceitar_nao_revela_se_o_email_existe(grupo_do_dono):
    """[003] ABU-2: com e-mail novo e convite inválido, ou e-mail existente e convite válido, a falha é a mesma."""
    codigo = gerar(grupo_do_dono)

    existente = aceitar(codigo, email="dono@example.com")[1]
    invalido_email_novo = aceitar("codigo-inexistente", email="nunca-usado@example.com")[1]

    assert (existente.status_code, existente.json()) == (
        invalido_email_novo.status_code,
        invalido_email_novo.json(),
    )
    assert "entrelinhas_sessionid" not in existente.cookies


def test_req_3_7_grupo_cheio_recusa_convite(grupo_do_dono):
    """[003] REQ-3.7: com dois membros não se gera convite."""
    codigo = gerar(grupo_do_dono)
    assert aceitar(codigo)[1].status_code == 201

    assert grupo_do_dono.postar("/api/v1/grupo/convites").status_code == 409


def test_req_2_3_grupo_cheio_recusa_entrada_por_qualquer_caminho(grupo_do_dono, novo_participante):
    """[003] REQ-2.3: mesmo com um convite pendente à força no banco, o terceiro não entra."""
    grupo = Grupo.objects.get()
    novo_participante("ana@example.com", nome="Ana", cor=ROXO, grupo=grupo)
    codigo = convite_pendente_a_forca()

    _, resposta = aceitar(codigo)

    assert resposta.status_code == 400
    assert resposta.json() == FALHA
    assert Perfil.objects.filter(grupo=grupo).count() == 2
    assert not get_user_model().objects.filter(email="bia@example.com").exists()


def test_nfr_sec_2_codigo_do_convite_tem_128_bits_e_so_o_hash_e_gravado(grupo_do_dono):
    """[003] NFR-SEC-2: o código tem ao menos 128 bits de aleatoriedade e o banco guarda só o SHA-256."""
    codigo = gerar(grupo_do_dono)

    convite = Convite.objects.get()
    assert len(codigo) >= 22  # 16 bytes em base64 sem preenchimento
    assert convite.codigo_hash == hashlib.sha256(codigo.encode()).hexdigest()
    valores = [str(v) for v in vars(convite).values()]
    assert codigo not in " ".join(valores)


def test_prop_3_codigo_so_uma_vez_e_nunca_gravado(grupo_do_dono):
    """[003] PROP-3: o código aparece só na resposta que o cria, não em outras rotas, e só vale uma vez."""
    codigo = gerar(grupo_do_dono)

    for rota in ("/api/v1/grupo", "/api/v1/perfil"):
        assert codigo not in grupo_do_dono.get(rota).content.decode()
    assert aceitar(codigo)[1].status_code == 201
    assert aceitar(codigo, email="outra@example.com")[1].status_code == 400


def test_abu_3_codigo_adivinhado_ou_reutilizado_recusado_sem_revelar(grupo_do_dono):
    """[003] ABU-3: chute e reuso dão a mesma resposta única."""
    codigo = gerar(grupo_do_dono)
    chutes = [aceitar(f"chute-{i}", email=f"c{i}@example.com")[1] for i in range(5)]
    assert aceitar(codigo)[1].status_code == 201

    reuso = aceitar(codigo, email="reuso@example.com")[1]

    for resposta in [*chutes, reuso]:
        assert (resposta.status_code, resposta.json()) == (400, FALHA)


@pytest.mark.django_db(transaction=True)
def test_prop_2_dois_aceites_simultaneos_no_ultimo_lugar_deixam_um_so(novo_participante, logar):
    """[003] PROP-2 / PROP-3: duas pessoas usam o mesmo código ao mesmo tempo: uma entra, a outra é recusada."""
    novo_participante("dono@example.com", nome="Dono", cor=VERDE)
    dono = logar("dono@example.com")
    assert dono.postar("/api/v1/grupo").status_code == 201
    codigo = gerar(dono)
    largada = threading.Barrier(2)

    def tentar(indice):
        try:
            cliente = Cliente()
            cliente.token()
            largada.wait(timeout=10)
            return cliente.postar(
                "/api/v1/convites/aceitar",
                dados_de_bia(codigo, email=f"pessoa{indice}@example.com"),
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = sorted(pool.map(tentar, [1, 2]))

    assert resultados == [201, 400]
    assert Perfil.objects.filter(grupo=Grupo.objects.get()).count() == 2
    assert get_user_model().objects.filter(email__startswith="pessoa").count() == 1
