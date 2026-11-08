"""Calendário do grupo (spec 009): lê os registros (só autor, dia e horário) e entrega o estado de cada dia. Sem texto."""

import logging
import re
from datetime import date

from apps.acesso.erros import ErroValidacao
from apps.acesso.models import Perfil
from apps.acesso.services import foto_url
from apps.registros import services as registros
from apps.registros.models import Registro

from . import domain

log = logging.getLogger("apps.calendario")
MES = re.compile(r"\d{4}-(0[1-9]|1[0-2])")


def _mes_valido(mes, hoje: date) -> tuple[int, int]:
    if not isinstance(mes, str) or not MES.fullmatch(mes):
        raise ErroValidacao({"mes": ["Informe o mês como AAAA-MM."]})
    ano, numero = int(mes[:4]), int(mes[5:])
    if (ano, numero) > (hoje.year, hoje.month):
        raise ErroValidacao({"mes": ["Esse mês ainda não chegou."]})
    return ano, numero


def calendario(usuario, mes) -> dict:
    hoje = registros.dia_de(registros.agora())
    ano, numero = _mes_valido(mes, hoje)
    vazio = {"mes": mes, "hoje": hoje.isoformat(), "membros": [], "dias": []}

    grupo_id = (
        Perfil.objects.filter(pk=usuario.pk).values_list("grupo_id", flat=True).first()
    )  # consulta 1
    if grupo_id is None:
        return vazio
    perfis = list(  # consulta 2
        Perfil.objects.filter(grupo_id=grupo_id).order_by("entrou_em", "usuario_id")
    )
    datas = [p.entrou_em for p in perfis if p.entrou_em]
    if datas and (ano, numero) < (min(datas).year, min(datas).month):
        log.info("calendario recusado: mes=%s anterior a entrada do grupo=%s", mes, grupo_id)
        raise ErroValidacao({"mes": ["O grupo ainda não existia nesse mês."]})

    primeiro = date(ano, numero, 1)
    proximo = date(ano + (numero == 12), numero % 12 + 1, 1)
    entregas = {  # consulta 3: só autor, dia e horário; nunca o texto
        (autor, data): quando
        for autor, data, quando in Registro.objects.filter(
            grupo_id=grupo_id,
            autor_id__in=[p.pk for p in perfis],
            data__gte=primeiro,
            data__lt=proximo,
        ).values_list("autor_id", "data", "entregue_em")
    }
    dias = domain.estado_do_mes(entregas, [(p.pk, p.entrou_em) for p in perfis], hoje, ano, numero)
    return {
        "mes": mes,
        "hoje": hoje.isoformat(),
        "membros": [
            {"nome": p.nome, "cor": p.cor, "foto_url": foto_url(p.foto_id)} for p in perfis
        ],
        "dias": [{**d, "data": d["data"].isoformat()} for d in dias],
    }
