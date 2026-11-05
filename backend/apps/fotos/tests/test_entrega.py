"""[004] Entrega, autorização por objeto, remoção, limpeza e cota."""

import io
import uuid
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone
from PIL import Image

from apps.fotos.models import Foto

from .conftest import apagar, arquivos_em, enviar_foto, imagem_bytes


def _enviar_manuscrito(cliente) -> str:
    resposta = enviar_foto(cliente, imagem_bytes("JPEG", (40, 30)))
    assert resposta.status_code == 201, resposta.content
    return resposta.json()["id"]


def test_req_6_5_dono_recebe_a_imagem_com_cabecalhos_fixos(dono):
    """[004] REQ-6.5: tipo fixo, sem cache compartilhado e sem sniffing."""
    foto_id = _enviar_manuscrito(dono)

    resposta = dono.get(f"/api/v1/fotos/{foto_id}/arquivo")

    assert resposta.status_code == 200
    assert resposta["Content-Type"] == "image/jpeg"
    assert resposta["Cache-Control"] == "private, no-store"
    assert resposta["X-Content-Type-Options"] == "nosniff"
    assert Image.open(io.BytesIO(b"".join(resposta.streaming_content))).size == (40, 30)


def test_req_6_6_outra_pessoa_do_mesmo_grupo_recebe_404_no_manuscrito(dono, parceiro):
    """[004] REQ-6.6: manuscrito é só do dono (a regra para o parceiro é da 005)."""
    foto_id = _enviar_manuscrito(dono)

    assert parceiro().get(f"/api/v1/fotos/{foto_id}/arquivo").status_code == 404


def test_req_6_6_pessoa_de_outro_grupo_recebe_404_no_manuscrito(dono, estranho):
    """[004] REQ-6.6 / ABU-6 / CTL-23: outro grupo recebe 404, nunca 403."""
    foto_id = _enviar_manuscrito(dono)

    assert estranho.get(f"/api/v1/fotos/{foto_id}/arquivo").status_code == 404


def test_abu_6_id_inexistente_ou_malformado_da_404(dono):
    """[004] ABU-6: trocar o id na URL só dá 404."""
    assert dono.get(f"/api/v1/fotos/{uuid.uuid4()}/arquivo").status_code == 404
    assert dono.get("/api/v1/fotos/nao-e-uuid/arquivo").status_code == 404


def test_req_6_6_anonimo_recebe_401(dono, cliente):
    """[004] REQ-1.4 estendido: sem sessão, nenhuma rota de foto responde."""
    foto_id = _enviar_manuscrito(dono)

    assert cliente.get(f"/api/v1/fotos/{foto_id}/arquivo").status_code == 401
    assert cliente.post("/api/v1/fotos", {}, format="json").status_code in (401, 403)


def test_req_6_7_dono_apaga_foto_avulsa_e_o_arquivo_some(dono, pasta_de_fotos):
    """[004] REQ-6.7: apagar remove o registro e o arquivo."""
    foto_id = _enviar_manuscrito(dono)
    assert len(arquivos_em(pasta_de_fotos)) == 1

    resposta = apagar(dono, f"/api/v1/fotos/{foto_id}")

    assert resposta.status_code == 204
    assert Foto.objects.count() == 0
    assert arquivos_em(pasta_de_fotos) == []


def test_req_6_7_so_o_dono_apaga(dono, parceiro, estranho):
    """[004] REQ-6.7 / CTL-23: foto de outra pessoa responde 404 e continua lá."""
    foto_id = _enviar_manuscrito(dono)

    assert apagar(parceiro(), f"/api/v1/fotos/{foto_id}").status_code == 404
    assert apagar(estranho, f"/api/v1/fotos/{foto_id}").status_code == 404
    assert Foto.objects.count() == 1


def test_req_6_8_foto_anexada_nao_pode_ser_apagada(dono, pasta_de_fotos):
    """[004] REQ-6.8: anexada a um registro ou ao perfil, a resposta é 409."""
    foto_id = _enviar_manuscrito(dono)
    Foto.objects.filter(pk=foto_id).update(anexada=True)

    resposta = apagar(dono, f"/api/v1/fotos/{foto_id}")

    assert resposta.status_code == 409
    assert Foto.objects.count() == 1
    assert len(arquivos_em(pasta_de_fotos)) == 1


def test_req_6_9_limpar_fotos_apaga_so_as_avulsas_com_mais_de_24_horas(dono, pasta_de_fotos):
    """[004] REQ-6.9: avulsa antiga some; avulsa recente e anexada antiga ficam."""
    antiga_avulsa = _enviar_manuscrito(dono)
    recente_avulsa = _enviar_manuscrito(dono)
    antiga_anexada = _enviar_manuscrito(dono)
    agora = timezone.now()
    Foto.objects.filter(pk=antiga_avulsa).update(criada_em=agora - timedelta(hours=25))
    Foto.objects.filter(pk=antiga_anexada).update(
        criada_em=agora - timedelta(hours=48), anexada=True
    )
    Foto.objects.filter(pk=recente_avulsa).update(criada_em=agora - timedelta(hours=23))

    call_command("limpar_fotos")

    assert set(map(str, Foto.objects.values_list("id", flat=True))) == {
        recente_avulsa,
        antiga_anexada,
    }
    nomes = " ".join(p.name for p in arquivos_em(pasta_de_fotos))
    assert antiga_avulsa not in nomes
    assert recente_avulsa in nomes
    assert antiga_anexada in nomes


def test_req_6_9_limpar_fotos_sem_nada_a_limpar_nao_falha(db):
    """[004] REQ-6.9: o comando é seguro de rodar a qualquer hora."""
    call_command("limpar_fotos")


def test_abu_7_vinte_envios_por_hora_depois_429(dono):
    """[004] ABU-7: o 21º envio dentro de uma hora é recusado."""
    for _ in range(20):
        assert enviar_foto(dono, imagem_bytes("JPEG", (8, 8))).status_code == 201
    # anexadas, para o teto de 30 avulsas não ser o motivo da recusa
    Foto.objects.update(anexada=True)

    resposta = enviar_foto(dono, imagem_bytes("JPEG", (8, 8)))

    assert resposta.status_code == 429
    assert "detalhe" in resposta.json()


def test_abu_7_envios_antigos_nao_contam_na_hora(dono):
    """[004] ABU-7: só a última hora conta."""
    for _ in range(20):
        enviar_foto(dono, imagem_bytes("JPEG", (8, 8)))
    Foto.objects.update(anexada=True, criada_em=timezone.now() - timedelta(hours=2))

    assert enviar_foto(dono, imagem_bytes("JPEG", (8, 8))).status_code == 201


def test_abu_7_trinta_fotos_avulsas_por_pessoa_e_o_teto(dono):
    """[004] ABU-7: com 30 avulsas na conta (fora da última hora), o próximo envio é recusado."""
    _enviar_manuscrito(dono)
    modelo = Foto.objects.get()
    for _ in range(29):
        Foto.objects.create(
            dono=modelo.dono,
            finalidade="manuscrito",
            tipo="image/jpeg",
            largura=8,
            altura=8,
            bytes=100,
            arquivo=f"{uuid.uuid4()}.jpg",
        )
    Foto.objects.update(criada_em=timezone.now() - timedelta(hours=2))
    assert Foto.objects.filter(anexada=False).count() == 30

    assert enviar_foto(dono, imagem_bytes("JPEG", (8, 8))).status_code == 429


@pytest.mark.django_db
def test_ctl_24_pasta_das_fotos_nao_e_publica(settings):
    """[004] CTL-24 / NFR-FOTO-1: nenhuma rota serve a pasta; ela está fora de static e media."""
    from django.urls import get_resolver

    pasta = str(settings.FOTOS_DIR)
    assert str(settings.STATIC_ROOT) not in pasta
    assert not getattr(settings, "MEDIA_ROOT", "")
    for padrao in get_resolver().url_patterns:
        assert "fotos_data" not in str(padrao.pattern)
        assert "media" not in str(padrao.pattern)
