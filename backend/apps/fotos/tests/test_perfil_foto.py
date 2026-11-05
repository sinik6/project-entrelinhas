"""[004] Foto de perfil: definir, trocar, remover, quem vê, grupo sem e-mail."""

from apps.fotos.models import Foto

from .conftest import apagar, arquivos_em, definir_foto_de_perfil, enviar_foto, imagem_bytes


def _enviar_de_perfil(cliente) -> str:
    resposta = enviar_foto(cliente, imagem_bytes("JPEG", (200, 100)), finalidade="perfil")
    assert resposta.status_code == 201, resposta.content
    return resposta.json()["id"]


def test_req_7_1_definir_foto_de_perfil_aparece_no_perfil(dono):
    """[004] REQ-7.1: depois de definir, o perfil traz o endereço da foto (relativo à base da API)."""
    foto_id = _enviar_de_perfil(dono)

    resposta = definir_foto_de_perfil(dono, foto_id)

    assert resposta.status_code == 200, resposta.content
    assert resposta.json()["foto_url"] == f"fotos/{foto_id}/arquivo"
    assert dono.get("/api/v1/perfil").json()["foto_url"] == f"fotos/{foto_id}/arquivo"
    assert Foto.objects.get(pk=foto_id).anexada is True


def test_req_7_1_perfil_sem_foto_traz_foto_url_nula(dono):
    """[004] REQ-7.1: sem foto, `foto_url` é nulo."""
    assert dono.get("/api/v1/perfil").json()["foto_url"] is None


def test_req_7_2_trocar_apaga_a_foto_anterior_registro_e_arquivo(dono, pasta_de_fotos):
    """[004] REQ-7.2: a foto anterior some por inteiro."""
    primeira = _enviar_de_perfil(dono)
    definir_foto_de_perfil(dono, primeira)
    segunda = _enviar_de_perfil(dono)

    resposta = definir_foto_de_perfil(dono, segunda)

    assert resposta.status_code == 200
    assert not Foto.objects.filter(pk=primeira).exists()
    assert Foto.objects.filter(pk=segunda).exists()
    assert primeira not in " ".join(p.name for p in arquivos_em(pasta_de_fotos))


def test_req_7_2_remover_apaga_a_foto_e_o_perfil_volta_sem_foto(dono, pasta_de_fotos):
    """[004] REQ-7.2: remover apaga e o perfil fica sem foto."""
    foto_id = _enviar_de_perfil(dono)
    definir_foto_de_perfil(dono, foto_id)

    resposta = apagar(dono, "/api/v1/perfil/foto")

    assert resposta.status_code == 204
    assert dono.get("/api/v1/perfil").json()["foto_url"] is None
    assert Foto.objects.count() == 0
    assert arquivos_em(pasta_de_fotos) == []


def test_req_7_2_remover_sem_foto_nao_falha(dono):
    """[004] REQ-7.2: remover de novo é seguro."""
    assert apagar(dono, "/api/v1/perfil/foto").status_code == 204


def test_req_7_3_grupo_traz_foto_dos_membros_e_nunca_o_email(dono, parceiro):
    """[004] REQ-7.3: nome, cor e foto de cada membro; o e-mail não aparece em lugar nenhum."""
    foto_id = _enviar_de_perfil(dono)
    definir_foto_de_perfil(dono, foto_id)
    bia = parceiro()

    corpo = bia.get("/api/v1/grupo").json()["grupo"]

    por_nome = {m["nome"]: m for m in corpo["membros"]}
    assert por_nome["Dono"]["foto_url"] == f"fotos/{foto_id}/arquivo"
    assert por_nome["Bia"]["foto_url"] is None
    assert "@" not in str(corpo)


def test_req_7_4_parceiro_ve_a_foto_de_perfil_e_o_estranho_recebe_404(dono, parceiro, estranho):
    """[004] REQ-7.4 / CTL-23: foto de perfil é do grupo; de fora, 404."""
    foto_id = _enviar_de_perfil(dono)
    definir_foto_de_perfil(dono, foto_id)

    assert parceiro().get(f"/api/v1/fotos/{foto_id}/arquivo").status_code == 200
    assert estranho.get(f"/api/v1/fotos/{foto_id}/arquivo").status_code == 404


def test_req_7_5_foto_de_manuscrito_nao_vira_foto_de_perfil(dono):
    """[004] REQ-7.5: finalidade errada é recusada."""
    resposta = enviar_foto(dono, imagem_bytes("JPEG"), finalidade="manuscrito")
    foto_id = resposta.json()["id"]

    saida = definir_foto_de_perfil(dono, foto_id)

    assert saida.status_code == 422
    assert "foto_id" in saida.json()["campos"]


def test_req_7_5_foto_de_outra_pessoa_ou_inexistente_tem_a_mesma_recusa(dono, parceiro):
    """[004] REQ-7.5 / ABU-6: não dá para usar foto alheia, e a resposta não diz se ela existe."""
    bia = parceiro()
    alheia = _enviar_de_perfil(bia)

    de_outra = definir_foto_de_perfil(dono, alheia)
    inexistente = definir_foto_de_perfil(dono, "00000000-0000-4000-8000-000000000000")
    malformada = definir_foto_de_perfil(dono, "isto-nao-e-uuid")

    assert de_outra.status_code == inexistente.status_code == malformada.status_code == 422
    assert de_outra.json() == inexistente.json() == malformada.json()


def test_req_7_5_foto_ja_anexada_em_outro_lugar_nao_serve(dono):
    """[004] REQ-7.5: só foto avulsa de perfil do próprio dono."""
    foto_id = _enviar_de_perfil(dono)
    Foto.objects.filter(pk=foto_id).update(anexada=True)

    assert definir_foto_de_perfil(dono, foto_id).status_code == 422
