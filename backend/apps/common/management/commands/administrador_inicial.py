"""Cria o superusuário inicial a partir do ambiente (spec 002).

Chamado pelo `infra/deploy.sh` com `docker compose run -e`: nome, e-mail e senha chegam só a esta
execução. Idempotente: usuário que já é superusuário não muda. A senha nunca é escrita.
"""

import os

from django.core.management.base import BaseCommand, CommandError

from apps.common.services import ErroAdministradorInicial, criar_administrador_inicial


class Command(BaseCommand):
    help = "Cria o superusuário inicial (ADMIN_USUARIO, ADMIN_EMAIL, SENHA_ADMIN_INICIAL)."

    def handle(self, *args, **options):
        try:
            usuario, criado = criar_administrador_inicial(
                usuario=os.environ.get("ADMIN_USUARIO", ""),
                email=os.environ.get("ADMIN_EMAIL", ""),
                senha=os.environ.get("SENHA_ADMIN_INICIAL", ""),
            )
        except ErroAdministradorInicial as erro:
            raise CommandError(str(erro)) from None
        situacao = "criado" if criado else "já existe"
        self.stdout.write(f"Administrador {situacao}: {usuario.get_username()}")
