"""Casos de uso dos registros (spec 005): entregar, ler, listar por mês. Não importa DRF e não lê o texto do registro."""

import logging
import re
import uuid
from datetime import date
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.acesso.erros import ErroConflito, ErroValidacao
from apps.acesso.models import Perfil
from apps.acesso.services import foto_url
from apps.fotos.erros import ErroNaoEncontrado
from apps.fotos.models import Foto

from . import domain
from .models import Registro

registro_log = logging.getLogger("apps.registros")
FUSO = ZoneInfo("America/Sao_Paulo")
MES = re.compile(r"\d{4}-(0[1-9]|1[0-2])")
MENSAGEM_JA_ENTREGOU = "Você já entregou o registro de hoje."
MENSAGEM_SEM_GRUPO = "Entre em um grupo antes de escrever."
MENSAGEM_FOTOS = "Escolha de 1 a 3 fotos suas, ainda não usadas."
FOTOS_MAXIMO = 3


def agora():
    """O instante da entrega. É uma função para o teste poder fixar a hora."""
    return timezone.now()


def dia_de(instante) -> date:
    return instante.astimezone(FUSO).date()


# ---------- apresentação (tudo passa por domain.visivel_para) ----------


def _autores(ids) -> dict:
    return {
        p.pk: {"nome": p.nome, "cor": p.cor, "foto_url": foto_url(p.foto_id)}
        for p in Perfil.objects.filter(pk__in=set(ids))
    }


def _fotos(ids) -> dict:
    por_registro: dict = {}
    consulta = Foto.objects.filter(registro_id__in=ids).order_by("ordem", "criada_em")
    for registro_id, foto_id in consulta.values_list("registro_id", "id"):
        por_registro.setdefault(registro_id, []).append(str(foto_id))
    return por_registro


def apresentar(registros: list[Registro], usuario) -> list[dict]:
    autores = _autores(r.autor_id for r in registros)
    fotos = _fotos([r.pk for r in registros])
    return [
        domain.visivel_para(r, usuario.pk, autores.get(r.autor_id, {}), fotos.get(r.pk, []))
        for r in registros
    ]


def _grupo_id_de(usuario_id):
    return Perfil.objects.filter(pk=usuario_id).values_list("grupo_id", flat=True).first()


def _pode_ler(registro: Registro, usuario) -> bool:
    """O autor lê os próprios registros sempre. O parceiro só lê se os dois ainda estão no grupo do registro:
    quem sai do grupo leva os registros, e quem entra depois não lê o que ficou (achado da auditoria da 005)."""
    if registro.autor_id == usuario.pk:
        return True
    grupo_id = _grupo_id_de(usuario.pk)
    return (
        grupo_id is not None
        and registro.grupo_id == grupo_id
        and _grupo_id_de(registro.autor_id) == grupo_id
    )


def _grupo_id(usuario):
    return Perfil.objects.filter(pk=usuario.pk).values_list("grupo_id", flat=True).first()


# ---------- entregar ----------


def _fotos_validas(usuario, ids) -> list[Foto]:
    """1 a 3 fotos de manuscrito do próprio autor, avulsas e sem repetição. Toda falha tem a mesma mensagem."""
    erro = ErroValidacao({"fotos": [MENSAGEM_FOTOS]})
    if not isinstance(ids, list) or not 1 <= len(ids) <= FOTOS_MAXIMO:
        raise erro
    try:
        unicos = [uuid.UUID(i) for i in ids if isinstance(i, str)]
    except ValueError:
        raise erro from None
    if len(unicos) != len(ids) or len(set(unicos)) != len(unicos):
        raise erro
    achadas = {
        f.pk: f
        for f in Foto.objects.select_for_update().filter(
            pk__in=unicos,
            dono=usuario,
            finalidade=Foto.Finalidade.MANUSCRITO,
            anexada=False,
            registro__isnull=True,
        )
    }
    if len(achadas) != len(unicos):
        raise erro
    return [achadas[i] for i in unicos]


def entregar(usuario, texto, visibilidade, trecho, fotos) -> dict:
    with transaction.atomic():
        # Travar o perfil serializa os pedidos da mesma pessoa: o segundo vê a entrega do primeiro e recebe 409.
        perfil = Perfil.objects.select_for_update().filter(pk=usuario.pk).first()
        if perfil is None or not perfil.grupo_id:
            raise ErroConflito(MENSAGEM_SEM_GRUPO)
        instante = agora()
        hoje = dia_de(instante)
        if Registro.objects.filter(autor=usuario, data=hoje).exists():
            raise ErroConflito(MENSAGEM_JA_ENTREGOU)

        texto = domain.validar_texto(texto)
        limites = domain.validar_visibilidade_e_trecho(visibilidade, trecho, texto)
        anexos = _fotos_validas(usuario, fotos)
        try:
            with transaction.atomic():
                registro = Registro.objects.create(
                    grupo_id=perfil.grupo_id,
                    autor=usuario,
                    data=hoje,
                    texto=texto,
                    visibilidade=visibilidade,
                    trecho_inicio=limites[0] if limites else None,
                    trecho_fim=limites[1] if limites else None,
                    entregue_em=instante,
                )
        except IntegrityError:
            raise ErroConflito(MENSAGEM_JA_ENTREGOU) from None
        for ordem, foto in enumerate(anexos):
            Foto.objects.filter(pk=foto.pk).update(registro=registro, anexada=True, ordem=ordem)
    # Só ids e contagens: nada do texto, do trecho nem dos arquivos (Art. 9).
    registro_log.info(
        "registro entregue id=%s autor=%s visibilidade=%s fotos=%s",
        registro.pk,
        usuario.pk,
        visibilidade,
        len(anexos),
    )
    return apresentar([registro], usuario)[0]


# ---------- ler ----------


def ler(usuario, registro_id) -> dict:
    try:
        identificador = uuid.UUID(str(registro_id))
    except ValueError:
        raise ErroNaoEncontrado from None
    registro = Registro.objects.filter(pk=identificador).first()
    if registro is None or not _pode_ler(registro, usuario):
        raise ErroNaoEncontrado
    return apresentar([registro], usuario)[0]


def _mes_valido(mes) -> tuple[int, int]:
    if not isinstance(mes, str) or not MES.fullmatch(mes):
        raise ErroValidacao({"mes": ["Informe o mês como AAAA-MM."]})
    ano, numero = int(mes[:4]), int(mes[5:])
    hoje = dia_de(agora())
    if (ano, numero) > (hoje.year, hoje.month):
        raise ErroValidacao({"mes": ["Esse mês ainda não chegou."]})
    return ano, numero


def listar_mes(usuario, mes) -> list[dict]:
    ano, numero = _mes_valido(mes)
    grupo_id = _grupo_id(usuario)
    inicio = date(ano, numero, 1)
    fim = date(ano + (numero == 12), numero % 12 + 1, 1)
    # Os próprios sempre; os do parceiro só enquanto os dois estão no grupo do registro.
    visiveis = Q(autor=usuario)
    if grupo_id:
        visiveis |= Q(grupo_id=grupo_id, autor__perfil__grupo_id=grupo_id)
    registros = list(
        Registro.objects.filter(visiveis, data__gte=inicio, data__lt=fim).order_by("-entregue_em")
    )
    return apresentar(registros, usuario)
