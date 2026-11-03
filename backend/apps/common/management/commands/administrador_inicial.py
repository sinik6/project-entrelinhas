"""Cria o superusuário inicial a partir do ambiente (spec 002).

Chamado pelo `infra/deploy.sh` com `docker compose run -e`: nome, e-mail e senha chegam só a esta
execução. Idempotente: usuário que já é superusuário não muda. A senha nunca é escrita.

`--verificar` só valida os valores e a política de senhas, sem consultar nem gravar no banco: o deploy
o roda antes de parar a API, para uma configuração ruim abortar com o Admin ainda no ar.
"""

import os

from django.core.management.base import BaseCommand, CommandError

from apps.common.services import (
    ErroAdministradorInicial,
    criar_administrador_inicial,
    validar_configuracao_do_administrador,
)


class Command(BaseCommand):
    help = "Cria o superusuário inicial (ADMIN_USUARIO, ADMIN_EMAIL, SENHA_ADMIN_INICIAL)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--verificar",
            action="store_true",
            help="Só valida nome, e-mail e senha (e a política de senhas); não usa o banco.",
        )

    def handle(self, *args, **options):
        valores = {
            "usuario": os.environ.get("ADMIN_USUARIO", ""),
            "email": os.environ.get("ADMIN_EMAIL", ""),
            "senha": os.environ.get("SENHA_ADMIN_INICIAL", ""),
        }
        try:
            if options["verificar"]:
                validar_configuracao_do_administrador(**valores)
                self.stdout.write("Configuração do administrador válida")
                return
            usuario, criado = criar_administrador_inicial(**valores)
        except ErroAdministradorInicial as erro:
            raise CommandError(str(erro)) from None
        situacao = "criado" if criado else "já existe"
        self.stdout.write(f"Administrador {situacao}: {usuario.get_username()}")
        if not usuario.is_active:
            # REQ-1.4: a conta existente não é alterada, mas o deploy verde não pode esconder que ninguém entra.
            self.stderr.write(
                f"AVISO: o superusuário {usuario.get_username()} está inativo e nada foi alterado."
            )
