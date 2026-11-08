"""Casos de uso dos destaques (spec 007). Não importa DRF e nunca lê o texto do registro: só `texto_visivel_para` (CTL-56)."""

import logging
import unicodedata
import uuid

from django.db import transaction
from django.utils import timezone

from apps.acesso.erros import ErroConflito, ErroValidacao
from apps.acesso.models import Perfil
from apps.fotos.erros import ErroNaoEncontrado
from apps.registros import domain
from apps.registros.models import Registro
from apps.registros.services import registro_legivel

from .erros import ErroProibido
from .models import Comentario, Destaque

log = logging.getLogger("apps.destaques")
DESTAQUES_POR_PESSOA = 50
COMENTARIOS_POR_DESTAQUE = 20
COMENTARIO_MAXIMO = 1000
SEM_TEXTO = "Este registro não tem texto para destacar."
_PERMITIDOS = ("\n", "\t")


def _uuid(valor):
    try:
        return uuid.UUID(str(valor))
    except ValueError:
        raise ErroNaoEncontrado from None


def _inteiro(valor) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_comentario(texto) -> str:
    """1 a 1000 caracteres úteis, sem controle (exceto quebra de linha e tabulação). A mensagem não repete o texto."""
    if not isinstance(texto, str) or not texto.strip():
        raise ErroValidacao({"texto": ["Escreva o comentário."]})
    if len(texto) > COMENTARIO_MAXIMO:
        raise ErroValidacao({"texto": [f"Use no máximo {COMENTARIO_MAXIMO} caracteres."]})
    for caractere in texto:
        categoria = unicodedata.category(caractere)
        if (categoria == "Cc" and caractere not in _PERMITIDOS) or categoria == "Cs":
            raise ErroValidacao(
                {"texto": ["O comentário tem caracteres que não podem ser usados."]}
            )
    return texto


def _texto_visivel(registro, usuario) -> str:
    visivel = domain.texto_visivel_para(registro, usuario.pk)
    if visivel is None:
        raise ErroConflito(SEM_TEXTO)
    return visivel


def _validar_posicao(inicio, fim, visivel: str) -> None:
    """Só o tamanho do texto VISÍVEL aparece na mensagem; a mesma para qualquer posição fora dele (ABU-14)."""
    if not _inteiro(inicio) or not _inteiro(fim):
        raise ErroValidacao({"inicio": ["Informe o início e o fim como números inteiros."]})
    if not 0 <= inicio < fim <= len(visivel):
        raise ErroValidacao(
            {
                "inicio": [
                    f"A posição precisa estar entre 0 e {len(visivel)}, com pelo menos um caractere."
                ]
            }
        )


# ---------- apresentação ----------


def _autores(ids) -> dict:
    return {p.pk: {"nome": p.nome, "cor": p.cor} for p in Perfil.objects.filter(pk__in=set(ids))}


def apresentar(destaques: list[Destaque], visivel: str, usuario) -> list[dict]:
    comentarios = {
        d.pk: list(d.comentarios.all()) for d in destaques
    }  # já com prefetch quando vem de `listar`
    autores = _autores(
        [d.autor_id for d in destaques] + [c.autor_id for cs in comentarios.values() for c in cs]
    )

    def comentario(c: Comentario) -> dict:
        return {
            "id": str(c.pk),
            "texto": c.texto,
            "autor": autores.get(c.autor_id, {}),
            "meu": c.autor_id == usuario.pk,
            "criado_em": c.criado_em.isoformat(),
            "editado_em": c.editado_em.isoformat() if c.editado_em else None,
        }

    return [
        {
            "id": str(d.pk),
            "inicio": d.inicio,
            "fim": d.fim,
            "trecho": visivel[d.inicio : d.fim],
            "autor": autores.get(d.autor_id, {}),
            "meu": d.autor_id == usuario.pk,
            "criado_em": d.criado_em.isoformat(),
            "comentarios": [comentario(c) for c in comentarios[d.pk]],
        }
        for d in destaques
    ]


# ---------- criar e listar ----------


def listar(usuario, registro_id) -> list[dict]:
    registro = registro_legivel(usuario, registro_id)
    visivel = _texto_visivel(registro, usuario)
    destaques = list(Destaque.objects.filter(registro=registro).prefetch_related("comentarios"))
    return apresentar(destaques, visivel, usuario)


def criar(usuario, registro_id, inicio, fim, comentario) -> dict:
    registro = registro_legivel(usuario, registro_id)
    visivel = _texto_visivel(registro, usuario)
    _validar_posicao(inicio, fim, visivel)
    texto = None if comentario is None else validar_comentario(comentario)
    with transaction.atomic():
        # Travar o registro serializa os pedidos: o limite de 50 vale também para pedidos simultâneos.
        Registro.objects.select_for_update().filter(pk=registro.pk).first()
        if (
            Destaque.objects.filter(registro=registro, autor=usuario).count()
            >= DESTAQUES_POR_PESSOA
        ):
            raise ErroConflito(f"Você já fez {DESTAQUES_POR_PESSOA} destaques neste registro.")
        destaque = Destaque.objects.create(registro=registro, autor=usuario, inicio=inicio, fim=fim)
        if texto is not None:
            Comentario.objects.create(destaque=destaque, autor=usuario, texto=texto)
    log.info(
        "destaque criado id=%s registro=%s autor=%s comentario=%s",
        destaque.pk,
        registro.pk,
        usuario.pk,
        texto is not None,
    )
    destaque = Destaque.objects.prefetch_related("comentarios").get(pk=destaque.pk)
    return apresentar([destaque], visivel, usuario)[0]


# ---------- por objeto ----------


def _destaque_do_grupo(usuario, destaque_id) -> Destaque:
    destaque = Destaque.objects.filter(pk=_uuid(destaque_id)).first()
    if destaque is None:
        raise ErroNaoEncontrado
    registro_legivel(usuario, destaque.registro_id)  # 404 se a pessoa não pode ler o registro
    return destaque


def _comentario_do_grupo(usuario, comentario_id) -> Comentario:
    comentario = (
        Comentario.objects.select_related("destaque").filter(pk=_uuid(comentario_id)).first()
    )
    if comentario is None:
        raise ErroNaoEncontrado
    registro_legivel(usuario, comentario.destaque.registro_id)
    return comentario


def apagar_destaque(usuario, destaque_id) -> None:
    destaque = _destaque_do_grupo(usuario, destaque_id)
    if destaque.autor_id != usuario.pk:
        raise ErroProibido
    destaque.delete()  # os comentários saem junto (CASCADE)
    log.info("destaque apagado id=%s autor=%s", destaque.pk, usuario.pk)


def comentar(usuario, destaque_id, texto) -> dict:
    destaque = _destaque_do_grupo(usuario, destaque_id)
    texto = validar_comentario(texto)
    with transaction.atomic():
        # Trava no destaque: o limite de 20 vale também para pedidos simultâneos.
        Destaque.objects.select_for_update().filter(pk=destaque.pk).first()
        if Comentario.objects.filter(destaque=destaque).count() >= COMENTARIOS_POR_DESTAQUE:
            raise ErroConflito(f"Este destaque já tem {COMENTARIOS_POR_DESTAQUE} comentários.")
        comentario = Comentario.objects.create(destaque=destaque, autor=usuario, texto=texto)
    log.info("comentario criado id=%s destaque=%s autor=%s", comentario.pk, destaque.pk, usuario.pk)
    return _comentario_para_dict(comentario, usuario)


def _comentario_para_dict(comentario: Comentario, usuario) -> dict:
    autor = _autores([comentario.autor_id]).get(comentario.autor_id, {})
    return {
        "id": str(comentario.pk),
        "texto": comentario.texto,
        "autor": autor,
        "meu": comentario.autor_id == usuario.pk,
        "criado_em": comentario.criado_em.isoformat(),
        "editado_em": comentario.editado_em.isoformat() if comentario.editado_em else None,
    }


def editar_comentario(usuario, comentario_id, texto) -> dict:
    comentario = _comentario_do_grupo(usuario, comentario_id)
    if comentario.autor_id != usuario.pk:
        raise ErroProibido
    comentario.texto = validar_comentario(texto)
    comentario.editado_em = timezone.now()
    comentario.save(update_fields=["texto", "editado_em"])
    log.info("comentario editado id=%s autor=%s", comentario.pk, usuario.pk)
    return _comentario_para_dict(comentario, usuario)


def apagar_comentario(usuario, comentario_id) -> None:
    comentario = _comentario_do_grupo(usuario, comentario_id)
    if comentario.autor_id != usuario.pk:
        raise ErroProibido
    comentario.delete()
    log.info("comentario apagado id=%s autor=%s", comentario.pk, usuario.pk)
