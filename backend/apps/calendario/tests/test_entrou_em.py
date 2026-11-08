"""[009] `Perfil.entrou_em`: gravada ao criar o grupo e ao entrar por convite; a migração preenche as contas existentes."""

from datetime import UTC, date

import pytest
from django.contrib.auth import get_user_model

from apps.acesso.models import Perfil

from .conftest import relogio  # noqa: F401


def test_req_16_3_criar_grupo_grava_a_data_de_entrada(novo_participante, logar, relogio):  # noqa: F811
    """[009] REQ-16.3 / CTL-62."""
    novo_participante("ana@example.com", nome="Ana")
    ana = logar("ana@example.com")
    relogio.fixar(2026, 11, 7, 2, 30)  # 23h30 de 06/11 em São Paulo

    assert ana.postar("/api/v1/grupo").status_code == 201

    assert Perfil.objects.get(nome="Ana").entrou_em == date(2026, 11, 6)


def test_req_16_3_aceitar_convite_grava_a_data_de_entrada(dono, relogio):  # noqa: F811
    """[009] REQ-16.3 / CTL-62."""
    relogio.fixar(2026, 11, 8, 12)
    codigo = dono.postar("/api/v1/grupo/convites").json()["codigo"]
    from apps.acesso.tests.conftest import Cliente

    novo = Cliente()
    resposta = novo.postar(
        "/api/v1/convites/aceitar",
        {
            "codigo": codigo,
            "nome": "Bia",
            "email": "bia@example.com",
            "senha": "uma-senha-bem-comprida-123",
            "cor": "#B45309",
        },
    )

    assert resposta.status_code in (200, 201), resposta.content
    assert Perfil.objects.get(nome="Bia").entrou_em == date(2026, 11, 8)


@pytest.mark.django_db
def test_req_16_3_preenchimento_das_contas_existentes_usa_a_data_de_criacao_em_sao_paulo():
    """[009] CTL-62: a função da migração preenche `entrou_em` com a data de criação da conta (fuso de São Paulo)."""
    from datetime import datetime

    from apps.acesso import preenchimento as m

    usuario = get_user_model().objects.create_user(
        username="velho@example.com", email="velho@example.com", password="x"
    )
    get_user_model().objects.filter(pk=usuario.pk).update(
        date_joined=datetime(2026, 11, 1, 2, 0, tzinfo=UTC)
    )
    Perfil.objects.create(usuario=usuario, nome="Velho", cor="#4D7C0F")

    m.preencher(Perfil)

    assert Perfil.objects.get(nome="Velho").entrou_em == date(
        2026, 10, 31
    )  # 23h de 31/10 em São Paulo
