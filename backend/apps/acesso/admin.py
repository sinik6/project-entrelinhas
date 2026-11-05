from django.contrib import admin

from .models import Convite, Grupo, Perfil


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "limite_membros", "criado_em")


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "nome", "cor", "grupo")


@admin.register(Convite)
class ConviteAdmin(admin.ModelAdmin):
    """Só leitura: o código nunca existe em claro e criar convite à mão pularia as regras do service."""

    list_display = ("grupo", "criado_em", "expira_em", "usado_em", "invalidado_em")
    readonly_fields = [campo.name for campo in Convite._meta.fields]

    def has_add_permission(self, request):
        return False
