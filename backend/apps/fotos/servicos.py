"""Regras das fotos (spec 004): validar, recodificar, guardar, autorizar, apagar. Não importa DRF."""

import io
import os
import uuid
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageOps

from apps.acesso.erros import ErroConflito, ErroValidacao
from apps.acesso.models import Perfil

from .erros import ErroLimite, ErroNaoEncontrado
from .models import Foto

LIMITE_BYTES = 8 * 1024 * 1024
LADO_MAXIMO = 4096
LADO_DO_PERFIL = 1024
PIXELS_MAXIMOS = 20_000_000  # 4096 x 4096 = 16,7 milhões cabe; acima disso é bomba de descompressão
ENVIOS_POR_HORA = 20
AVULSAS_POR_PESSOA = 30
IDADE_DA_AVULSA = timedelta(hours=24)
# Defesa em profundidade: o Pillow também recusa imagens com pixels demais já ao abrir.
Image.MAX_IMAGE_PIXELS = PIXELS_MAXIMOS

FORMATOS = {  # formato do Pillow -> (tipo, extensão)
    "JPEG": ("image/jpeg", "jpg"),
    "PNG": ("image/png", "png"),
    "WEBP": ("image/webp", "webp"),
}
MENSAGEM_INVALIDA = "Envie uma foto em JPEG, PNG ou WebP."
MENSAGEM_PERFIL = "Foto inválida."
_METADADOS = ("icc_profile", "exif", "comment", "xmp", "dpi", "photoshop", "transparency_extra")


@dataclass
class Processada:
    dados: bytes
    tipo: str
    extensao: str
    largura: int
    altura: int


def pasta():
    return settings.FOTOS_DIR


def caminho_do_arquivo(foto: Foto):
    return pasta() / foto.arquivo


def _recusa(mensagem: str):
    raise ErroValidacao({"arquivo": [mensagem]})


def processar(dados: bytes, finalidade: str) -> Processada:
    """Decodifica e regrava a imagem: o que sai é uma imagem nova, do tipo que o servidor decide, sem metadados."""
    if len(dados) > LIMITE_BYTES:
        _recusa("A foto passa de 8 MB. Envie uma menor.")
    try:
        with Image.open(io.BytesIO(dados)) as aberta:
            formato = aberta.format
            if formato not in FORMATOS:
                _recusa(MENSAGEM_INVALIDA)
            largura, altura = aberta.size
            if max(largura, altura) > LADO_MAXIMO:
                _recusa(f"A foto passa de {LADO_MAXIMO} px de lado. Envie uma menor.")
            if largura * altura > PIXELS_MAXIMOS:
                _recusa("A foto tem pixels demais. Envie uma menor.")
            aberta.load()
            imagem = ImageOps.exif_transpose(
                aberta
            )  # aplica a rotação do celular antes de descartar o EXIF
    except ErroValidacao:
        raise
    except (OSError, ValueError, SyntaxError, EOFError, Image.DecompressionBombError):
        _recusa(MENSAGEM_INVALIDA)

    for chave in _METADADOS:
        imagem.info.pop(chave, None)
    if finalidade == "perfil":
        imagem.thumbnail((LADO_DO_PERFIL, LADO_DO_PERFIL))
    tipo, extensao = FORMATOS[formato]
    opcoes: dict = {}
    if formato == "JPEG":
        if imagem.mode not in ("RGB", "L"):
            imagem = imagem.convert("RGB")
        opcoes = {"quality": 90, "optimize": True}
    elif formato == "PNG":
        opcoes = {"optimize": True}
    else:
        opcoes = {"quality": 90}
    saida = io.BytesIO()
    imagem.save(saida, formato, **opcoes)
    largura, altura = imagem.size
    return Processada(saida.getvalue(), tipo, extensao, largura, altura)


def _conferir_cota(usuario) -> None:
    agora = timezone.now()
    na_hora = Foto.objects.filter(dono=usuario, criada_em__gte=agora - timedelta(hours=1)).count()
    avulsas = Foto.objects.filter(dono=usuario, anexada=False).count()
    if na_hora >= ENVIOS_POR_HORA or avulsas >= AVULSAS_POR_PESSOA:
        raise ErroLimite("Muitas fotos enviadas. Tente mais tarde.")


def enviar(usuario, arquivo, finalidade: str) -> Foto:
    if finalidade not in Foto.Finalidade.values:
        raise ErroValidacao({"finalidade": ["Escolha manuscrito ou perfil."]})
    if arquivo is None:
        raise ErroValidacao({"arquivo": ["Escolha uma foto."]})
    _conferir_cota(usuario)
    processada = processar(arquivo.read(LIMITE_BYTES + 1), finalidade)

    identificador = uuid.uuid4()
    nome = f"{identificador}.{processada.extensao}"
    with transaction.atomic():
        foto = Foto.objects.create(
            id=identificador,
            dono=usuario,
            finalidade=finalidade,
            tipo=processada.tipo,
            largura=processada.largura,
            altura=processada.altura,
            bytes=len(processada.dados),
            arquivo=nome,
        )
        _gravar(foto, processada.dados)  # se falhar, a transação desfaz o registro
    return foto


def _gravar(foto: Foto, dados: bytes) -> None:
    destino = caminho_do_arquivo(foto)
    destino.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporario = destino.with_name(destino.name + ".tmp")
    temporario.write_bytes(dados)
    os.replace(temporario, destino)


def _remover_arquivo(foto: Foto) -> None:
    caminho_do_arquivo(foto).unlink(missing_ok=True)


def apagar_foto(foto: Foto) -> None:
    """Remove o registro e o arquivo. Quem chama já decidiu que pode."""
    arquivo = caminho_do_arquivo(foto)
    foto.delete()
    arquivo.unlink(missing_ok=True)


# ---------- autorização ----------


def _grupo_de(usuario_id) -> object | None:
    return Perfil.objects.filter(pk=usuario_id).values_list("grupo_id", flat=True).first()


def pode_ver(usuario, foto: Foto) -> bool:
    """Manuscrito: só o dono (a regra do parceiro é de `registros`). Perfil: o dono e o grupo dele."""
    if foto.dono_id == usuario.pk:
        return True
    if foto.finalidade == Foto.Finalidade.PERFIL:
        grupo = _grupo_de(foto.dono_id)
        return grupo is not None and grupo == _grupo_de(usuario.pk)
    return False


def foto_visivel(usuario, foto_id) -> Foto:
    try:
        foto_id = uuid.UUID(str(foto_id))
    except ValueError:
        raise ErroNaoEncontrado from None
    foto = Foto.objects.filter(pk=foto_id).first()
    if foto is None or not pode_ver(usuario, foto):
        raise ErroNaoEncontrado
    return foto


def apagar_avulsa(usuario, foto_id) -> None:
    try:
        foto_id = uuid.UUID(str(foto_id))
    except ValueError:
        raise ErroNaoEncontrado from None
    foto = Foto.objects.select_for_update().filter(pk=foto_id, dono=usuario).first()
    if foto is None:
        raise ErroNaoEncontrado
    if foto.anexada:
        raise ErroConflito("Esta foto já está em uso e não pode ser apagada.")
    apagar_foto(foto)


def limpar_avulsas_antigas() -> int:
    limite = timezone.now() - IDADE_DA_AVULSA
    antigas = list(Foto.objects.filter(anexada=False, criada_em__lt=limite))
    for foto in antigas:
        apagar_foto(foto)
    return len(antigas)


# ---------- foto de perfil ----------


def definir_foto_de_perfil(usuario, foto_id) -> None:
    perfil = Perfil.objects.select_for_update().filter(pk=usuario.pk).first()
    if perfil is None:
        raise ErroValidacao({"perfil": ["Informe seu nome e sua cor antes de escolher a foto."]})
    try:
        identificador = uuid.UUID(str(foto_id))
    except ValueError:
        raise ErroValidacao({"foto_id": [MENSAGEM_PERFIL]}) from None
    foto = (
        Foto.objects.select_for_update()
        .filter(pk=identificador, dono=usuario, finalidade=Foto.Finalidade.PERFIL, anexada=False)
        .first()
    )
    if foto is None:
        raise ErroValidacao({"foto_id": [MENSAGEM_PERFIL]})
    anterior = Foto.objects.filter(pk=perfil.foto_id).first() if perfil.foto_id else None
    foto.anexada = True
    foto.save(update_fields=["anexada"])
    perfil.foto = foto
    perfil.save(update_fields=["foto"])
    if anterior is not None:
        apagar_foto(anterior)


def remover_foto_de_perfil(usuario) -> None:
    perfil = Perfil.objects.select_for_update().filter(pk=usuario.pk).first()
    if perfil is None or not perfil.foto_id:
        return
    foto = Foto.objects.get(pk=perfil.foto_id)
    perfil.foto = None
    perfil.save(update_fields=["foto"])
    apagar_foto(foto)
