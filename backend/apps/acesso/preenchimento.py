"""Preenchimento de `Perfil.entrou_em` das contas que já existiam (spec 009): a data de criação da conta, em São Paulo."""

from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")


def preencher(perfil_model) -> int:
    """Recebe o modelo `Perfil` (o real ou o histórico da migração). Só toca em quem ainda não tem a data."""
    total = 0
    for perfil in perfil_model.objects.filter(entrou_em__isnull=True).select_related("usuario"):
        perfil.entrou_em = perfil.usuario.date_joined.astimezone(FUSO).date()
        perfil.save(update_fields=["entrou_em"])
        total += 1
    return total
