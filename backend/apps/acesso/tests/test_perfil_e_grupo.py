"""[003] Perfil, senha e grupo (US-2, US-4): regras e isolamento entre grupos."""

import pytest

from apps.acesso.models import Grupo
from apps.acesso.tests.conftest import AMBAR, CIANO, OUTRA_SENHA, ROXO, SENHA, VERDE, Cliente


def test_req_4_9_perfil_incompleto_da_conta_do_administrador(novo_participante, logar):
    """[003] REQ-4.9: conta sem nome e cor (a do administrador) é indicada como incompleta."""
    novo_participante("dono@example.com", nome=None)

    perfil = logar("dono@example.com").get("/api/v1/perfil").json()

    assert perfil["completo"] is False
    assert perfil["nome"] is None
    assert perfil["cor"] is None
    assert perfil["email"] == "dono@example.com"
    assert perfil["grupo"] is None


def test_req_2_4_perfil_incompleto_nao_cria_grupo(novo_participante, logar):
    """[003] REQ-2.4: sem nome e cor não há grupo."""
    novo_participante("dono@example.com", nome=None)

    resposta = logar("dono@example.com").postar("/api/v1/grupo")

    assert resposta.status_code == 422
    assert Grupo.objects.count() == 0


def test_req_4_2_define_nome_e_cor_da_conta_sem_perfil(novo_participante, logar):
    """[003] REQ-4.2: o administrador completa o perfil pela primeira vez, com a cor guardada em maiúsculas."""
    novo_participante("dono@example.com", nome=None)
    cliente = logar("dono@example.com")

    resposta = cliente.alterar("/api/v1/perfil", {"nome": "  Dono  ", "cor": CIANO.lower()})

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Dono"
    assert resposta.json()["cor"] == CIANO
    assert resposta.json()["completo"] is True


def test_req_4_2_primeiro_perfil_exige_nome_e_cor_juntos(novo_participante, logar):
    """[003] REQ-4.2 / NFR-SEC-3: criar o perfil só com o nome, sem cor, é recusado."""
    novo_participante("dono@example.com", nome=None)

    resposta = logar("dono@example.com").alterar("/api/v1/perfil", {"nome": "Dono"})

    assert resposta.status_code == 422
    assert "cor" in resposta.json()["campos"]


def test_req_4_2_altera_so_o_nome(novo_participante, logar):
    """[003] REQ-4.2: depois de completo, dá para mudar só o nome ou só a cor."""
    novo_participante("ana@example.com", nome="Ana", cor=VERDE)
    cliente = logar("ana@example.com")

    resposta = cliente.alterar("/api/v1/perfil", {"nome": "Ana Maria"})

    assert resposta.json()["nome"] == "Ana Maria"
    assert resposta.json()["cor"] == VERDE


@pytest.mark.parametrize("nome", ["", "   ", "a" * 61, "Ana\x00", "Ana\nMaria", "Ana‮Maria"])
def test_nfr_sec_3_nome_invalido_recusado_no_backend(novo_participante, logar, nome):
    """[003] NFR-SEC-3: nome vazio, longo ou com caractere de controle é recusado com 422."""
    novo_participante("ana@example.com")

    resposta = logar("ana@example.com").alterar("/api/v1/perfil", {"nome": nome})

    assert resposta.status_code == 422
    assert "nome" in resposta.json()["campos"]


@pytest.mark.parametrize("cor", ["vermelho", "#FFF", "#GGGGGG", "0E7490", "", None])
def test_req_4_3_cor_fora_do_formato_recusada(novo_participante, logar, cor):
    """[003] REQ-4.3 / NFR-SEC-3: a API recusa cor fora de `#RRGGBB`."""
    novo_participante("ana@example.com")

    resposta = logar("ana@example.com").alterar("/api/v1/perfil", {"cor": cor})

    assert resposta.status_code == 422
    assert "cor" in resposta.json()["campos"]


@pytest.mark.parametrize("cor", ["#FFFFFF", "#000000", "#FFFF00", "#1D4ED8"])
def test_req_4_4_cor_ilegivel_recusada(novo_participante, logar, cor):
    """[003] REQ-4.4 / NFR-SEC-3: a API recusa cor com contraste menor que 3 para 1."""
    novo_participante("ana@example.com")

    resposta = logar("ana@example.com").alterar("/api/v1/perfil", {"cor": cor})

    assert resposta.status_code == 422
    assert "cor" in resposta.json()["campos"]


def test_req_4_5_cor_igual_ou_indistinguivel_recusada(novo_participante, logar, novo_grupo):
    """[003] REQ-4.5: a cor da outra pessoa do grupo, ou uma quase igual, é recusada; uma bem diferente passa."""
    grupo = novo_grupo()
    novo_participante("ana@example.com", nome="Ana", cor=AMBAR, grupo=grupo)
    novo_participante("bia@example.com", nome="Bia", cor=VERDE, grupo=grupo)
    cliente = logar("bia@example.com")

    igual = cliente.alterar("/api/v1/perfil", {"cor": AMBAR})
    parecida = cliente.alterar("/api/v1/perfil", {"cor": "#C2410C"})
    diferente = cliente.alterar("/api/v1/perfil", {"cor": ROXO})

    assert igual.status_code == parecida.status_code == 422
    assert diferente.status_code == 200


def test_req_4_5_cor_de_quem_esta_em_outro_grupo_nao_conta(novo_participante, logar, novo_grupo):
    """[003] REQ-4.5: só a cor da outra pessoa do mesmo grupo importa."""
    novo_participante("ana@example.com", nome="Ana", cor=AMBAR, grupo=novo_grupo())
    novo_participante("bia@example.com", nome="Bia", cor=VERDE, grupo=novo_grupo())

    assert logar("bia@example.com").alterar("/api/v1/perfil", {"cor": AMBAR}).status_code == 200


def test_req_2_1_cria_grupo(novo_participante, logar):
    """[003] REQ-2.1: quem tem perfil completo e nenhum grupo cria o grupo, como único membro."""
    novo_participante("ana@example.com", nome="Ana", cor=VERDE)
    cliente = logar("ana@example.com")

    resposta = cliente.postar("/api/v1/grupo")

    assert resposta.status_code == 201
    grupo = resposta.json()
    assert grupo["tipo"] == "escrita"
    assert grupo["limite_membros"] == 2
    assert grupo["membros"] == [{"nome": "Ana", "cor": VERDE}]
    assert grupo["vaga"] is True
    assert cliente.get("/api/v1/grupo").json()["grupo"] == grupo


def test_req_2_2_segundo_grupo_recusado(grupo_do_dono):
    """[003] REQ-2.2: quem já tem grupo não cria outro."""
    resposta = grupo_do_dono.postar("/api/v1/grupo")

    assert resposta.status_code == 409
    assert Grupo.objects.count() == 1


def test_req_2_1_sem_grupo_a_consulta_devolve_nulo(novo_participante, logar):
    """[003] REQ-2.1: sem grupo, GET /grupo devolve `{grupo: null}` (e não 404)."""
    novo_participante("ana@example.com")

    assert logar("ana@example.com").get("/api/v1/grupo").json() == {"grupo": None}


def test_req_4_1_perfil(grupo_do_dono):
    """[003] REQ-4.1: o perfil traz nome, e-mail, cor e o grupo."""
    perfil = grupo_do_dono.get("/api/v1/perfil").json()

    assert perfil["nome"] == "Dono"
    assert perfil["email"] == "dono@example.com"
    assert perfil["cor"] == VERDE
    assert perfil["completo"] is True
    assert perfil["grupo"]["membros"] == [{"nome": "Dono", "cor": VERDE}]


def test_req_4_8_grupo_mostra_nome_e_cor_do_parceiro_e_nunca_o_email(
    novo_participante, logar, novo_grupo
):
    """[003] REQ-4.8: o parceiro aparece só com nome e cor; o e-mail dele não está em lugar nenhum da resposta."""
    grupo = novo_grupo()
    novo_participante("ana@example.com", nome="Ana", cor=VERDE, grupo=grupo)
    novo_participante("bia@example.com", nome="Bia", cor=AMBAR, grupo=grupo)
    cliente = logar("ana@example.com")

    corpo = cliente.get("/api/v1/grupo")
    perfil = cliente.get("/api/v1/perfil")

    assert {"nome": "Bia", "cor": AMBAR} in corpo.json()["grupo"]["membros"]
    for resposta in (corpo, perfil):
        assert "bia@example.com" not in resposta.content.decode()


def test_req_isolamento_cada_participante_so_enxerga_o_proprio_grupo(
    novo_participante, logar, novo_grupo
):
    """[003] CTL-17: não há como ver membros ou convites de outro grupo; as rotas nem recebem identificador."""
    novo_participante("ana@example.com", nome="Ana", cor=VERDE, grupo=novo_grupo())
    novo_participante("bia@example.com", nome="Bia", cor=AMBAR, grupo=novo_grupo())
    cliente = logar("ana@example.com")

    membros = cliente.get("/api/v1/grupo").json()["grupo"]["membros"]
    convite = cliente.postar("/api/v1/grupo/convites")

    assert [m["nome"] for m in membros] == ["Ana"]
    assert convite.status_code == 201
    assert Grupo.objects.count() == 2


def test_req_4_6_troca_senha_encerra_as_outras_sessoes(novo_participante, logar):
    """[003] REQ-4.6: trocar a senha mantém a sessão atual e derruba a de outro aparelho."""
    novo_participante("ana@example.com")
    celular, notebook = logar("ana@example.com"), logar("ana@example.com")

    resposta = notebook.postar(
        "/api/v1/perfil/senha", {"senha_atual": SENHA, "senha_nova": OUTRA_SENHA}
    )

    assert resposta.status_code == 204
    assert notebook.get("/api/v1/perfil").status_code == 200
    assert celular.get("/api/v1/perfil").status_code == 401
    assert Cliente().entrar("ana@example.com", OUTRA_SENHA).status_code == 200
    assert Cliente().entrar("ana@example.com", SENHA).status_code == 400


@pytest.mark.parametrize(
    ("atual", "nova", "campo"),
    [
        ("senha-errada-1234567", OUTRA_SENHA, "senha_atual"),
        (SENHA, "curta1!", "senha_nova"),
        (SENHA, "123456789012", "senha_nova"),
        (SENHA, "password1234", "senha_nova"),
        (SENHA, "ana@example.com", "senha_nova"),
    ],
)
def test_req_4_7_senha_atual_errada_ou_nova_fraca_recusadas(
    novo_participante, logar, atual, nova, campo
):
    """[003] REQ-4.7 / NFR-SEC-3: nada muda quando a senha atual está errada ou a nova não atende à política."""
    novo_participante("ana@example.com")
    cliente = logar("ana@example.com")

    resposta = cliente.postar("/api/v1/perfil/senha", {"senha_atual": atual, "senha_nova": nova})

    assert resposta.status_code == 422
    assert campo in resposta.json()["campos"]
    assert Cliente().entrar("ana@example.com", SENHA).status_code == 200
