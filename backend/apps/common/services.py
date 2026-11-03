"""Regras de negócio compartilhadas da capacidade `base`. Não importa DRF."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction


class ErroAdministradorInicial(Exception):
    """Configuração ou estado que impede criar o administrador inicial."""


def validar_configuracao_do_administrador(
    *, usuario: str, email: str, senha: str
) -> tuple[str, str]:
    """Valida nome, e-mail e senha do administrador inicial, sem consultar o banco (spec 002).

    Devolve `(usuario, email)` já sem espaços nas pontas. Nenhuma mensagem de erro repete a senha.
    """
    modelo = get_user_model()
    # Mesma normalização (NFKC) que `create_superuser` aplica: sem ela, a busca por um nome em forma
    # não normalizada não acharia a conta que já existe.
    usuario = modelo.normalize_username((usuario or "").strip())
    email = (email or "").strip()
    if not usuario or not email:
        raise ErroAdministradorInicial("ADMIN_USUARIO e ADMIN_EMAIL são obrigatórios.")
    if not senha or not senha.strip():
        raise ErroAdministradorInicial("SENHA_ADMIN_INICIAL é obrigatória e não pode ser vazia.")

    try:
        modelo._meta.get_field(modelo.USERNAME_FIELD).run_validators(usuario)
    except ValidationError as erro:
        raise ErroAdministradorInicial(
            "ADMIN_USUARIO inválido: " + " ".join(erro.messages)
        ) from None
    try:
        validate_email(email)
    except ValidationError:
        raise ErroAdministradorInicial("ADMIN_EMAIL inválido.") from None
    try:
        validate_password(senha, user=modelo(username=usuario, email=email))
    except ValidationError as erro:
        raise ErroAdministradorInicial(
            "Senha recusada pela política de senhas: " + " ".join(erro.messages)
        ) from None
    return usuario, email


def criar_administrador_inicial(*, usuario: str, email: str, senha: str) -> tuple[object, bool]:
    """Cria o superusuário inicial se ele ainda não existir (spec 002).

    Devolve `(usuario, criado)`. Usuário que já é superusuário fica como está, sem trocar senha nem e-mail.
    """
    usuario, email = validar_configuracao_do_administrador(
        usuario=usuario, email=email, senha=senha
    )

    modelo = get_user_model()
    existente = _buscar(modelo, usuario)
    if existente is not None:
        return _reaproveitar(existente), False

    try:
        with transaction.atomic():
            criado = modelo.objects.create_superuser(username=usuario, email=email, password=senha)
    except IntegrityError:
        # Outra execução criou o mesmo usuário no intervalo: trata como "já existe".
        concorrente = _encontrar(modelo, usuario)
        if concorrente is None:
            raise ErroAdministradorInicial(
                "Conflito ao criar o administrador; rode o deploy de novo."
            ) from None
        return _reaproveitar(concorrente), False
    return criado, True


def _buscar(modelo, usuario: str):
    """Procura o usuário pelo nome, sem diferenciar maiúsculas de minúsculas (`Dono` e `dono` são o mesmo)."""
    return _encontrar(modelo, usuario)


def _encontrar(modelo, usuario: str):
    return modelo.objects.filter(username__iexact=usuario).order_by("pk").first()


def _reaproveitar(existente):
    if not existente.is_superuser:
        raise ErroAdministradorInicial(
            f"O usuário {existente.get_username()} existe e não é superusuário; nada foi alterado."
        )
    return existente
