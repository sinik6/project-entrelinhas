"""[005] Quem sai do grupo leva os próprios registros; quem entra depois não lê o que ficou (achado 1 da auditoria independente)."""

from django.utils import timezone

from apps.acesso.models import Grupo, Perfil

from .conftest import entregar


def _mes():
    return f"{timezone.localdate():%Y-%m}"


def _cenario(dono, parceiro, novo_participante, logar, relogio):
    """Dono entrega `full` e `partial`; depois sai (vai para outro grupo) e Carla entra no grupo de origem."""
    bia = parceiro()
    grupo_de_origem = Perfil.objects.get(usuario__email="dono@example.com").grupo
    relogio.fixar(2026, 11, 5)
    cheio = entregar(dono, texto="~000~~001~~002~~003~").json()
    relogio.fixar(2026, 11, 6)
    parcial = entregar(
        dono, texto="~000~~001~~002~~003~", visibilidade="partial", trecho={"inicio": 5, "fim": 10}
    ).json()
    relogio.fixar(2026, 11, 20)
    outro = Grupo.objects.create()
    Perfil.objects.filter(usuario__email="dono@example.com").update(grupo=outro)
    novo_participante("carla@example.com", nome="Carla", cor="#9333EA", grupo=grupo_de_origem)
    return bia, logar("carla@example.com"), cheio, parcial


def test_req_9_8_membro_novo_do_grupo_nao_le_registros_de_quem_saiu(
    dono, parceiro, novo_participante, logar, relogio
):
    """[005] REQ-9.8 / CTL-40: o registro `full` e o `partial` de quem saiu não aparecem para Carla (lista, detalhe e foto)."""
    _, carla, cheio, parcial = _cenario(dono, parceiro, novo_participante, logar, relogio)

    assert carla.get("/api/v1/registros?mes=2026-11").json() == []
    assert carla.get(f"/api/v1/registros/{cheio['id']}").status_code == 404
    assert carla.get(f"/api/v1/registros/{parcial['id']}").status_code == 404
    assert carla.get(f"/api/v1/fotos/{cheio['fotos'][0]}/arquivo").status_code == 404


def test_req_9_8_quem_ficou_no_grupo_tambem_nao_le_o_de_quem_saiu(
    dono, parceiro, novo_participante, logar, relogio
):
    """[005] REQ-9.8 / CTL-40: Bia, que continua no grupo de origem, não lê o que Dono escreveu antes de sair."""
    bia, _, cheio, _ = _cenario(dono, parceiro, novo_participante, logar, relogio)

    assert bia.get("/api/v1/registros?mes=2026-11").json() == []
    assert bia.get(f"/api/v1/registros/{cheio['id']}").status_code == 404
    assert bia.get(f"/api/v1/fotos/{cheio['fotos'][0]}/arquivo").status_code == 404


def test_req_9_1_quem_saiu_continua_lendo_os_proprios_registros(
    dono, parceiro, novo_participante, logar, relogio
):
    """[005] REQ-9.1 / REQ-10.1: o autor lê o que escreveu mesmo depois de mudar de grupo."""
    _, _, cheio, parcial = _cenario(dono, parceiro, novo_participante, logar, relogio)

    detalhe = dono.get(f"/api/v1/registros/{cheio['id']}")
    lista = dono.get("/api/v1/registros?mes=2026-11").json()

    assert detalhe.status_code == 200
    assert detalhe.json()["texto"] == "~000~~001~~002~~003~"
    assert [r["id"] for r in lista] == [parcial["id"], cheio["id"]]
    assert dono.get(f"/api/v1/fotos/{cheio['fotos'][0]}/arquivo").status_code == 200


def test_req_10_3_sem_grupo_o_autor_ainda_lista_os_proprios_registros(
    dono, relogio, novo_participante
):
    """[005] REQ-10.3: sem grupo a pessoa vê só os seus (nenhum, se nunca escreveu)."""
    relogio.fixar(2026, 11, 5)
    meu = entregar(dono).json()["id"]
    Perfil.objects.filter(usuario__email="dono@example.com").update(grupo=None)

    assert [r["id"] for r in dono.get("/api/v1/registros?mes=2026-11").json()] == [meu]
    assert dono.get(f"/api/v1/registros/{meu}").status_code == 200


def test_req_9_2_quem_continua_no_grupo_segue_lendo_o_registro_full(dono, parceiro, relogio):
    """[005] REQ-9.2: a regra nova não atrapalha o caso normal."""
    bia = parceiro()
    relogio.fixar(2026, 11, 5)
    registro = entregar(dono).json()

    assert bia.get(f"/api/v1/registros/{registro['id']}").status_code == 200
    assert bia.get(f"/api/v1/fotos/{registro['fotos'][0]}/arquivo").status_code == 200
    assert len(bia.get("/api/v1/registros?mes=2026-11").json()) == 1


def test_req_9_8_foto_de_registro_do_grupo_antigo_nao_vai_ao_novo_parceiro(
    dono, parceiro, novo_participante, logar, relogio
):
    """[005] REQ-9.8 / CTL-40: Dono troca de grupo e passa a dividir o grupo com Eva; Eva não lê a foto de um registro do grupo antigo."""
    parceiro()
    relogio.fixar(2026, 11, 5)
    cheio = entregar(dono).json()
    outro = Grupo.objects.create()
    novo_participante("eva@example.com", nome="Eva", cor="#9333EA", grupo=outro)
    Perfil.objects.filter(usuario__email="dono@example.com").update(grupo=outro)
    eva = logar("eva@example.com")

    assert eva.get(f"/api/v1/fotos/{cheio['fotos'][0]}/arquivo").status_code == 404
    assert eva.get(f"/api/v1/registros/{cheio['id']}").status_code == 404
    assert eva.get("/api/v1/registros?mes=2026-11").json() == []
