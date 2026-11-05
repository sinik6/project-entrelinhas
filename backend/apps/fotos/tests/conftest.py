# ruff: noqa: F811
# (as fábricas da 003 são importadas e depois pedidas pelo nome nos parâmetros, o que o ruff lê como redefinição)
"""Suporte dos testes da 004: fábricas de imagem (JPEG, PNG, WebP, com EXIF, poliglotas) e pasta de fotos descartável."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

# Reusa as fábricas de participante e grupo da 003 (cliente com CSRF de verdade, logar, grupo_do_dono).
from apps.acesso.tests.conftest import (  # noqa: F401
    AMBAR,
    OUTRA_SENHA,
    SENHA,
    VERDE,
    Cliente,
    cliente,
    grupo_do_dono,
    logar,
    novo_grupo,
    novo_participante,
)

SEGREDO_EXIF = b"CAMERA-SECRETA-123"


@pytest.fixture(autouse=True)
def pasta_de_fotos(settings, tmp_path):
    """Cada teste grava numa pasta própria e a apaga sozinha (tmp_path)."""
    settings.FOTOS_DIR = tmp_path / "fotos"
    return settings.FOTOS_DIR


def arquivos_em(pasta) -> list:
    return [p for p in pasta.rglob("*") if p.is_file()] if pasta.exists() else []


def imagem_bytes(formato="JPEG", tamanho=(64, 48), exif=False) -> bytes:
    """Imagem válida, com ruído suave para não virar um arquivo trivial. `exif=True` grava marca de câmera e GPS."""
    imagem = Image.new("RGB", tamanho, (200, 120, 40))
    imagem.putpixel((0, 0), (1, 2, 3))
    saida = io.BytesIO()
    opcoes = {}
    if exif:
        dados = Image.Exif()
        dados[0x010F] = SEGREDO_EXIF.decode()  # Make
        dados[0x0110] = "MODELO-SECRETO"  # Model
        gps = dados.get_ifd(0x8825)
        gps[1], gps[2], gps[3], gps[4] = "S", (10.0, 0.0, 0.0), "W", (48.0, 0.0, 0.0)
        opcoes["exif"] = dados
    imagem.save(saida, formato, **opcoes)
    return saida.getvalue()


def enviar_foto(
    cliente, conteudo: bytes, nome="foto.jpg", tipo="image/jpeg", finalidade="manuscrito"
):
    arquivo = SimpleUploadedFile(nome, conteudo, content_type=tipo)
    return cliente.post(
        "/api/v1/fotos",
        {"arquivo": arquivo, "finalidade": finalidade},
        format="multipart",
        HTTP_X_CSRFTOKEN=cliente.token(),
    )


def apagar(cliente, url):
    return cliente.delete(url, HTTP_X_CSRFTOKEN=cliente.token())


def definir_foto_de_perfil(cliente, foto_id):
    return cliente.put(
        "/api/v1/perfil/foto", {"foto_id": foto_id}, format="json", HTTP_X_CSRFTOKEN=cliente.token()
    )


@pytest.fixture
def dono(grupo_do_dono):
    """O dono logado, com perfil e grupo."""
    return grupo_do_dono


@pytest.fixture
def parceiro(db, novo_participante, logar):
    """Segunda pessoa, no mesmo grupo do dono (o `dono` precisa ser pedido antes)."""

    def criar():
        from apps.acesso.models import Perfil

        grupo = Perfil.objects.get(usuario__email="dono@example.com").grupo
        novo_participante("par@example.com", nome="Bia", cor=AMBAR, grupo=grupo)
        return logar("par@example.com")

    return criar


@pytest.fixture
def estranho(db, novo_participante, novo_grupo, logar):
    """Uma pessoa de outro grupo."""
    novo_participante("fora@example.com", nome="Caio", cor="#9333EA", grupo=novo_grupo())
    return logar("fora@example.com")
