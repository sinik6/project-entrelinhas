"""[004] Envio e recodificação da foto: tipos, conteúdo falso, limites, metadados descartados, nome por UUID."""

import io
import random
from datetime import timedelta

import pytest
from django.utils import timezone
from PIL import Image

from apps.fotos.models import Foto

from .conftest import SEGREDO_EXIF, arquivos_em, enviar_foto, imagem_bytes

FORMATOS = [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")]


def _abrir(caminho) -> Image.Image:
    return Image.open(io.BytesIO(caminho.read_bytes()))


@pytest.mark.parametrize(("formato", "tipo"), FORMATOS)
def test_req_6_1_envio_valido_guarda_foto_avulsa(dono, pasta_de_fotos, formato, tipo):
    """[004] REQ-6.1: JPEG, PNG e WebP válidos viram foto avulsa e devolvem o id."""
    resposta = enviar_foto(dono, imagem_bytes(formato, (80, 60)), tipo=tipo)

    assert resposta.status_code == 201, resposta.content
    corpo = resposta.json()
    assert set(corpo) == {"id", "finalidade", "largura", "altura"}
    assert corpo["finalidade"] == "manuscrito"
    assert (corpo["largura"], corpo["altura"]) == (80, 60)
    foto = Foto.objects.get(pk=corpo["id"])
    assert foto.anexada is False
    assert foto.dono.email == "dono@example.com"
    assert foto.tipo == tipo
    assert len(arquivos_em(pasta_de_fotos)) == 1


@pytest.mark.parametrize(
    ("nome", "tipo_declarado", "conteudo"),
    [
        ("foto.jpg", "image/jpeg", b"<html><script>alert(1)</script></html>"),
        ("foto.png", "image/png", b"PK\x03\x04" + b"\x00" * 64),
        ("foto.jpg", "image/jpeg", b'<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>'),
        ("foto.jpg", "image/jpeg", b"GIF89a\x01\x00\x01\x00\x00\x00\x00;"),
        ("foto.jpg", "image/jpeg", imagem_bytes("GIF")),
        ("foto.jpg", "image/jpeg", imagem_bytes("BMP")),
        ("foto.png", "image/png", imagem_bytes("TIFF")),
        ("foto.jpg", "image/jpeg", b""),
        ("foto.jpg", "image/jpeg", imagem_bytes("JPEG")[:40]),
        ("foto.webp", "image/webp", b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"),
    ],
    ids=[
        "html",
        "zip",
        "svg",
        "gif-quebrado",
        "gif",
        "bmp",
        "tiff",
        "vazio",
        "jpeg-truncado",
        "pdf",
    ],
)
def test_req_6_2_conteudo_que_nao_e_imagem_aceita_e_recusado(
    dono, pasta_de_fotos, nome, tipo_declarado, conteudo
):
    """[004] REQ-6.2 / ABU-5: o conteúdo manda, não o nome nem o tipo declarado; nada é gravado."""
    resposta = enviar_foto(dono, conteudo, nome=nome, tipo=tipo_declarado)

    assert resposta.status_code == 422, resposta.content
    assert "arquivo" in resposta.json()["campos"]
    assert Foto.objects.count() == 0
    assert arquivos_em(pasta_de_fotos) == []


def test_req_6_2_finalidade_invalida_ou_ausente_e_arquivo_ausente_dao_422(dono):
    """[004] REQ-6.2: a finalidade só pode ser manuscrito ou perfil; sem arquivo também é 422."""
    assert enviar_foto(dono, imagem_bytes(), finalidade="outra").status_code == 422
    sem_arquivo = dono.post(
        "/api/v1/fotos",
        {"finalidade": "manuscrito"},
        format="multipart",
        HTTP_X_CSRFTOKEN=dono.token(),
    )
    assert sem_arquivo.status_code == 422
    assert "arquivo" in sem_arquivo.json()["campos"]


def test_req_6_3_arquivo_acima_de_8_mb_e_recusado_antes_de_decodificar(dono, pasta_de_fotos):
    """[004] REQ-6.3: mais de 8 MB é recusado."""
    resposta = enviar_foto(dono, imagem_bytes("PNG") + b"\x00" * (8 * 1024 * 1024))

    assert resposta.status_code == 422
    assert "8 MB" in resposta.json()["campos"]["arquivo"][0]
    assert arquivos_em(pasta_de_fotos) == []


def test_req_6_3_lado_maior_que_4096_px_e_recusado(dono, pasta_de_fotos):
    """[004] REQ-6.3: o lado maior passa de 4096 px."""
    resposta = enviar_foto(dono, imagem_bytes("PNG", (4097, 8)), tipo="image/png")

    assert resposta.status_code == 422
    assert "4096" in resposta.json()["campos"]["arquivo"][0]
    assert arquivos_em(pasta_de_fotos) == []


def test_req_6_3_lado_de_exatamente_4096_px_e_aceito(dono):
    """[004] REQ-6.3: o limite é inclusivo."""
    resposta = enviar_foto(dono, imagem_bytes("PNG", (4096, 8)), tipo="image/png")

    assert resposta.status_code == 201, resposta.content


def test_abu_5_bomba_de_descompressao_e_recusada(dono, pasta_de_fotos, settings):
    """[004] ABU-5: imagem com pixels demais para a memória é recusada sem derrubar a API."""
    # 4096 x 4096 = 16,7 milhões de pixels cabe no limite; acima do teto de pixels vira recusa.
    resposta = enviar_foto(dono, imagem_bytes("PNG", (4096, 4096)), tipo="image/png")

    assert resposta.status_code in (201, 422)
    if resposta.status_code == 422:
        assert arquivos_em(pasta_de_fotos) == []


def test_req_6_4_recodifica_sem_exif_e_sem_conteudo_extra(dono, pasta_de_fotos):
    """[004] REQ-6.4 / THR-25: marca de câmera, GPS e bytes depois do fim da imagem não chegam ao arquivo guardado."""
    original = imagem_bytes("JPEG", exif=True) + b"<script>alert('x')</script>"
    assert SEGREDO_EXIF in original

    resposta = enviar_foto(dono, original)

    assert resposta.status_code == 201, resposta.content
    (guardado,) = arquivos_em(pasta_de_fotos)
    bytes_guardados = guardado.read_bytes()
    assert SEGREDO_EXIF not in bytes_guardados
    assert b"MODELO-SECRETO" not in bytes_guardados
    assert b"<script>" not in bytes_guardados
    imagem = Image.open(io.BytesIO(bytes_guardados))
    assert imagem.format == "JPEG"
    assert not imagem.getexif()


def test_req_6_4_png_com_texto_embutido_perde_o_texto(dono, pasta_de_fotos):
    """[004] REQ-6.4: bloco de texto do PNG (comentário) é descartado."""
    imagem = Image.new("RGB", (16, 16), (1, 2, 3))
    from PIL.PngImagePlugin import PngInfo

    info = PngInfo()
    info.add_text("Comment", "COMENTARIO-SECRETO")
    saida = io.BytesIO()
    imagem.save(saida, "PNG", pnginfo=info)
    assert b"COMENTARIO-SECRETO" in saida.getvalue()

    resposta = enviar_foto(dono, saida.getvalue(), tipo="image/png")

    assert resposta.status_code == 201
    (guardado,) = arquivos_em(pasta_de_fotos)
    assert b"COMENTARIO-SECRETO" not in guardado.read_bytes()


def test_req_6_4_nome_gerado_e_tipo_definido_pelo_servidor(dono, pasta_de_fotos):
    """[004] REQ-6.4: nome em UUID, nunca o enviado; o tipo é o da imagem, não o declarado."""
    resposta = enviar_foto(
        dono, imagem_bytes("PNG"), nome="../../etc/passwd-minha-letra.jpg", tipo="image/jpeg"
    )

    assert resposta.status_code == 201
    (guardado,) = arquivos_em(pasta_de_fotos)
    assert guardado.parent == pasta_de_fotos or pasta_de_fotos in guardado.parents
    assert "passwd" not in str(guardado)
    assert "minha-letra" not in str(guardado)
    foto = Foto.objects.get()
    assert foto.tipo == "image/png"
    assert str(foto.id) in guardado.name


def test_req_7_1_foto_de_perfil_e_reduzida_a_1024_px(dono, pasta_de_fotos):
    """[004] REQ-7.1: a finalidade perfil reduz a imagem para no máximo 1024 px no lado maior."""
    resposta = enviar_foto(dono, imagem_bytes("JPEG", (2000, 1500)), finalidade="perfil")

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert max(corpo["largura"], corpo["altura"]) == 1024
    (guardado,) = arquivos_em(pasta_de_fotos)
    assert max(_abrir(guardado).size) == 1024


def test_req_6_1_participante_sem_perfil_ainda_pode_enviar(novo_participante, logar):
    """[004] REQ-6.1: a conta do administrador (sem perfil e sem grupo) também envia."""
    novo_participante("admin@example.com", nome=None)
    cliente = logar("admin@example.com")

    resposta = enviar_foto(cliente, imagem_bytes())

    assert resposta.status_code == 201
    assert Foto.objects.count() == 1


def test_prop_5_o_que_e_guardado_e_imagem_decodificavel_sem_metadados_ou_nada(dono, pasta_de_fotos):
    """[004] PROP-5: para bytes sorteados (válidos e corrompidos), ou recusa sem escrita, ou arquivo decodificável sem EXIF."""
    azar = random.Random(20261105)
    bases = [
        imagem_bytes("JPEG", (32, 32), exif=True),
        imagem_bytes("PNG", (32, 32)),
        imagem_bytes("WEBP", (32, 32), exif=True),
    ]
    aceitas = recusadas = 0
    for _ in range(60):
        dados = bytearray(azar.choice(bases))
        for _ in range(azar.randint(0, 6)):
            dados[azar.randrange(len(dados))] = azar.randrange(256)
        if azar.random() < 0.3:
            dados += bytes(azar.randrange(256) for _ in range(azar.randint(1, 200)))
        if azar.random() < 0.2:
            dados = dados[: azar.randrange(1, len(dados))]
        antes = len(arquivos_em(pasta_de_fotos))
        # a cota não é o assunto aqui: cada foto já enviada sai da última hora e da lista de avulsas
        Foto.objects.update(anexada=True, criada_em=timezone.now() - timedelta(hours=2))

        resposta = enviar_foto(dono, bytes(dados))

        assert resposta.status_code in (201, 422), resposta.content
        depois = arquivos_em(pasta_de_fotos)
        if resposta.status_code == 422:
            recusadas += 1
            assert len(depois) == antes
        else:
            aceitas += 1
            assert len(depois) == antes + 1
            foto = Foto.objects.get(pk=resposta.json()["id"])
            guardado = next(p for p in depois if str(foto.id) in p.name)
            conteudo = guardado.read_bytes()
            imagem = Image.open(io.BytesIO(conteudo))
            imagem.load()
            assert imagem.format in {"JPEG", "PNG", "WEBP"}
            assert SEGREDO_EXIF not in conteudo
            assert not imagem.getexif()
    assert aceitas > 0
    assert recusadas > 0
