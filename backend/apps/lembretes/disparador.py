"""O disparador do lembrete diário (spec 010): às 21h30 de São Paulo, só a quem ainda não entregou o dia.

A marca do dia (`LembreteEnviado`) é gravada ANTES do envio e é única por pessoa e dia: dois processos, ou um reinício no meio,
nunca duplicam um aviso (ABU-23). Uma falha de envio não é repetida no mesmo dia (REQ-19.8).
"""

import json
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction

from apps.acesso.models import Perfil
from apps.registros.models import Registro

from .models import AssinaturaPush, LembreteEnviado

log = logging.getLogger("apps.lembretes")
SP = ZoneInfo("America/Sao_Paulo")
INICIO = time(21, 30)
FIM = time(23, 0)  # exclusive: depois das 23h00 o dia é pulado
RETENCAO_DIAS = 30
CARGA = json.dumps(
    {"titulo": "Entrelinhas", "corpo": "Hora de escrever o seu dia.", "url": "#/hoje"},
    ensure_ascii=False,
)


def _candidatos(hoje: date) -> list:
    """Quem tem aparelho, tem grupo, ainda não entregou hoje e ainda não foi marcado hoje."""
    com_aparelho = set(AssinaturaPush.objects.values_list("usuario_id", flat=True))
    com_grupo = set(
        Perfil.objects.filter(pk__in=com_aparelho, grupo__isnull=False).values_list("pk", flat=True)
    )
    entregaram = set(
        Registro.objects.filter(autor_id__in=com_grupo, data=hoje).values_list(
            "autor_id", flat=True
        )
    )
    marcados = set(LembreteEnviado.objects.filter(data=hoje).values_list("usuario_id", flat=True))
    return sorted(com_grupo - entregaram - marcados)


def _marcar(usuario_id, hoje: date) -> bool:
    """Grava a marca do dia; `False` se outro processo (ou uma execução anterior) já a gravou."""
    try:
        with transaction.atomic():
            LembreteEnviado.objects.create(usuario_id=usuario_id, data=hoje)
        return True
    except IntegrityError:
        return False


def enviar_lembretes(agora: datetime, enviar) -> dict:
    """`agora` com fuso; `enviar(assinatura, carga)` devolve `ok`, `gone` ou `falha`. Devolve só contagens."""
    resumo = {"enviados": 0, "removidos": 0, "falhas": 0, "pessoas": 0}
    local = agora.astimezone(SP)
    if not INICIO <= local.time() < FIM:
        return resumo
    hoje = local.date()
    for usuario_id in _candidatos(hoje):
        if not _marcar(usuario_id, hoje):
            continue
        resumo["pessoas"] += 1
        # Quem entregou entre a consulta e agora não precisa mais do aviso (a marca fica, o dia está resolvido).
        if Registro.objects.filter(autor_id=usuario_id, data=hoje).exists():
            continue
        for assinatura in list(AssinaturaPush.objects.filter(usuario_id=usuario_id)):
            try:
                resultado = enviar(assinatura, CARGA)
            except Exception:
                resultado = "falha"
            if resultado == "ok":
                resumo["enviados"] += 1
            elif resultado == "gone":
                assinatura.delete()
                resumo["removidos"] += 1
            else:
                resumo["falhas"] += 1
    log.info(
        "lembretes dia=%s enviados=%s removidos=%s falhas=%s",
        hoje,
        resumo["enviados"],
        resumo["removidos"],
        resumo["falhas"],
    )
    return resumo


def limpar_marcas_antigas(hoje: date) -> int:
    apagadas, _ = LembreteEnviado.objects.filter(
        data__lt=hoje - timedelta(days=RETENCAO_DIAS)
    ).delete()
    return apagadas
