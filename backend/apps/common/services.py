"""Regras de negócio compartilhadas da capacidade `base`. Não importa DRF."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction


class ErroAdministradorInicial(Exception):
    """Configuração ou estado que impede criar o administrador inicial."""


def criar_administrador_inicial(*, usuario: str, email: str, senha: str) -> tuple[object, bool]:
    """Cria o superusuário inicial se ele ainda não existir (spec 002).

    Devolve `(usuario, criado)`. Usuário que já é superusuário fica como está, sem trocar senha nem e-mail.
    Nenhuma mensagem de erro repete a senha.
    """
    usuario = (usuario or "").strip()
    email = (email or "").strip()
    if not usuario or not email:
        raise ErroAdministradorInicial("ADMIN_USUARIO e ADMIN_EMAIL são obrigatórios.")
    if not senha or not senha.strip():
        raise ErroAdministradorInicial("SENHA_ADMIN_INICIAL é obrigatória e não pode ser vazia.")

    modelo = get_user_model()
    existente = modelo.objects.filter(username=usuario).first()
    if existente is not None:
        return _reaproveitar(existente), False

    try:
        validate_password(senha, user=modelo(username=usuario, email=email))
    except ValidationError as erro:
        raise ErroAdministradorInicial(
            "Senha recusada pela política de senhas: " + " ".join(erro.messages)
        ) from None

    try:
        with transaction.atomic():
            criado = modelo.objects.create_superuser(username=usuario, email=email, password=senha)
    except IntegrityError:
        # Outra execução criou o mesmo usuário no intervalo: trata como "já existe".
        return _reaproveitar(modelo.objects.get(username=usuario)), False
    return criado, True


def _reaproveitar(existente):
    if not existente.is_superuser:
        raise ErroAdministradorInicial(
            f"O usuário {existente.get_username()} existe e não é superusuário; nada foi alterado."
        )
    return existente
