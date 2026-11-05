"""[003] Regra de cor do perfil (REQ-4.3, REQ-4.4, REQ-4.5, PROP-1). Contra o oráculo: valores calculados à parte."""

import pytest

from apps.acesso import domain


@pytest.mark.parametrize(
    ("valor", "esperado"), [("#0e7490", "#0E7490"), ("#0E7490", "#0E7490"), ("#b45309", "#B45309")]
)
def test_req_4_3_cor_valida_e_normalizada_para_maiusculas(valor, esperado):
    """[003] REQ-4.3: `#RRGGBB` (em qualquer caixa) é aceito e guardado em maiúsculas."""
    assert domain.normalizar_cor(valor) == esperado


@pytest.mark.parametrize(
    "valor",
    [
        "red",
        "#FFF",
        "#GGGGGG",
        "0E7490",
        "#0E74901",
        "",
        " #0E7490",
        "#0E7490 ",
        "#0E7490\n",
        None,
        123,
    ],
)
def test_req_4_3_cor_fora_do_formato_recusada(valor):
    """[003] REQ-4.3: qualquer coisa fora de `#RRGGBB` é recusada, inclusive espaço nas pontas."""
    with pytest.raises(domain.CorInvalida):
        domain.normalizar_cor(valor)


def test_prop_1_contraste_conhecido():
    """[003] PROP-1: preto sobre branco dá 21 para 1 (valor da definição do WCAG)."""
    assert domain.contraste("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert domain.contraste("#FFFFFF", "#FFFFFF") == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("cor", "legivel"),
    [
        ("#FFFFFF", False),  # some no tema claro
        ("#000000", False),  # some no tema escuro
        ("#FFFF00", False),  # amarelo some no claro
        ("#1D4ED8", False),  # azul escuro: 2,80 para 1 no tema escuro
        ("#606060", False),  # 2,98 no escuro: logo abaixo do limite
        ("#626262", True),  # 3,07 no escuro
        ("#929292", True),  # 3,11 no claro
        ("#969696", False),  # 2,96 no claro: logo acima do limite
        ("#767676", True),
        ("#0E7490", True),
        ("#B45309", True),
    ],
)
def test_prop_1_contraste_minimo_3_para_1_nos_dois_temas(cor, legivel):
    """[003] PROP-1 / REQ-4.4: aceita se e somente se o contraste for ao menos 3 para 1 com o claro e com o escuro."""
    assert domain.cor_legivel(cor) is legivel


def test_prop_1_varredura_de_cinzas_so_aceita_o_intervalo_central():
    """[003] PROP-1: dos 256 cinzas, só os de 0x61 a 0x94 passam (limites calculados à parte com a fórmula do WCAG)."""
    aceitos = {g for g in range(256) if domain.cor_legivel(f"#{g:02X}{g:02X}{g:02X}")}

    assert aceitos == set(range(0x61, 0x95))


@pytest.mark.parametrize(
    ("a", "b", "distinguiveis"),
    [
        ("#0E7490", "#0E7490", False),  # igual
        ("#FF0000", "#FE0000", False),  # quase igual
        ("#B45309", "#C2410C", False),  # laranjas parecidos
        ("#4D7C0F", "#B45309", True),
        ("#9333EA", "#BE185D", True),
    ],
)
def test_req_4_5_cor_igual_ou_indistinguivel_recusada(a, b, distinguiveis):
    """[003] REQ-4.5: a diferença de cor (CIE76) precisa ser de pelo menos 25, e não importa a ordem."""
    assert domain.cores_distinguiveis(a, b) is distinguiveis
    assert domain.cores_distinguiveis(b, a) is distinguiveis
