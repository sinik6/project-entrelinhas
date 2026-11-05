"""Regras de negócio do acesso (spec 003). Não importa DRF: levanta erros de `erros.py` e as views traduzem."""

import hashlib
import secrets
import unicodedata
from datetime import timedelta

from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.utils import timezone

from . import domain
from .erros import ErroConflito, ErroGenerico, ErroValidacao
from .models import Convite, Grupo, Perfil

MENSAGEM_LOGIN = "E-mail ou senha incorretos."
MENSAGEM_CONVITE = "Não foi possível usar este convite."
VALIDADE_DO_CONVITE = timedelta(days=7)
NOME_MAX = 60
EMAIL_MAX = 150  # o e-mail vira o nome de usuário, que no Django tem 150 caracteres
BACKEND_PADRAO = "django.contrib.auth.backends.ModelBackend"


# ---------- leitura ----------


def _perfil_de(usuario) -> Perfil | None:
    return Perfil.objects.select_related("grupo").filter(pk=usuario.pk).first()


def foto_url(foto_id) -> str | None:
    """Endereço da foto de perfil, relativo à base da API (o app monta o resto com o prefixo da instalação)."""
    return f"fotos/{foto_id}/arquivo" if foto_id else None


def grupo_para_dict(grupo: Grupo) -> dict:
    """Do parceiro só nome e cor: o e-mail nunca sai daqui (REQ-4.8)."""
    membros = list(grupo.perfis.order_by("usuario__date_joined", "usuario_id"))
    return {
        "id": str(grupo.id),
        "tipo": grupo.tipo,
        "limite_membros": grupo.limite_membros,
        "membros": [
            {"nome": m.nome, "cor": m.cor, "foto_url": foto_url(m.foto_id)} for m in membros
        ],
        "vaga": len(membros) < grupo.limite_membros,
    }


def perfil_para_dict(usuario) -> dict:
    perfil = _perfil_de(usuario)
    return {
        "email": usuario.email,
        "nome": perfil.nome if perfil else None,
        "cor": perfil.cor if perfil else None,
        "foto_url": foto_url(perfil.foto_id) if perfil else None,
        "completo": perfil is not None,
        "grupo": grupo_para_dict(perfil.grupo) if perfil and perfil.grupo_id else None,
    }


def grupo_de(usuario) -> dict | None:
    perfil = _perfil_de(usuario)
    return grupo_para_dict(perfil.grupo) if perfil and perfil.grupo_id else None


# ---------- sessão ----------


def entrar(request, email: str, senha: str):
    email = (email or "").strip().lower()
    usuario = authenticate(request, email=email, password=senha)
    if usuario is None:
        raise ErroGenerico(MENSAGEM_LOGIN)
    login(request, usuario)  # renova a chave da sessão
    return usuario


def sair(request) -> None:
    logout(request)


# ---------- validações de campo ----------


def _nome_valido(nome: str) -> str:
    nome = (nome or "").strip()
    if not nome:
        raise ErroValidacao({"nome": ["Informe seu nome."]})
    if len(nome) > NOME_MAX:
        raise ErroValidacao({"nome": [f"Use no máximo {NOME_MAX} caracteres."]})
    if any(unicodedata.category(c).startswith("C") for c in nome):
        raise ErroValidacao({"nome": ["O nome tem caracteres que não podem ser usados."]})
    return nome


def _cor_valida(cor, cores_do_parceiro: list[str]) -> str:
    try:
        cor = domain.normalizar_cor(cor)
    except domain.CorInvalida as erro:
        raise ErroValidacao({"cor": [str(erro)]}) from None
    if not domain.cor_legivel(cor):
        raise ErroValidacao(
            {"cor": ["Essa cor fica ilegível no tema claro ou no escuro. Escolha outra."]}
        )
    if any(not domain.cores_distinguiveis(cor, outra) for outra in cores_do_parceiro):
        raise ErroValidacao(
            {"cor": ["Essa cor é igual ou parecida demais com a da outra pessoa do grupo."]}
        )
    return cor


def _email_valido(email: str) -> str:
    email = (email or "").strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        raise ErroValidacao({"email": ["Informe um e-mail válido."]}) from None
    if len(email) > EMAIL_MAX:
        raise ErroValidacao({"email": [f"Use no máximo {EMAIL_MAX} caracteres."]})
    return email


def _senha_valida(senha: str, usuario_de_referencia) -> str:
    try:
        validate_password(senha, user=usuario_de_referencia)
    except ValidationError as erro:
        raise ErroValidacao({"senha": list(erro.messages)}) from None
    return senha


def _juntar(erros: dict[str, list[str]], chamada) -> object | None:
    """Roda uma validação e acumula o erro por campo, para devolver todos juntos."""
    try:
        return chamada()
    except ErroValidacao as erro:
        for campo, mensagens in erro.campos.items():
            erros.setdefault(campo, []).extend(mensagens)
        return None


def _cores_dos_outros(perfil_ou_grupo_id, excluir_usuario_id=None) -> list[str]:
    if perfil_ou_grupo_id is None:
        return []
    consulta = Perfil.objects.filter(grupo_id=perfil_ou_grupo_id)
    if excluir_usuario_id is not None:
        consulta = consulta.exclude(pk=excluir_usuario_id)
    return list(consulta.values_list("cor", flat=True))


# ---------- perfil e senha ----------


def atualizar_perfil(usuario, nome=None, cor=None) -> dict:
    perfil = _perfil_de(usuario)
    erros: dict[str, list[str]] = {}
    if perfil is None:
        if nome is None:
            erros["nome"] = ["Informe seu nome."]
        if cor is None:
            erros["cor"] = ["Escolha uma cor."]
    nome_novo = _juntar(erros, lambda: _nome_valido(nome)) if nome is not None else None
    grupo_id = perfil.grupo_id if perfil else None
    cor_nova = (
        _juntar(erros, lambda: _cor_valida(cor, _cores_dos_outros(grupo_id, usuario.pk)))
        if cor is not None
        else None
    )
    if erros:
        raise ErroValidacao(erros)
    if perfil is None:
        Perfil.objects.create(usuario=usuario, nome=nome_novo, cor=cor_nova)
    else:
        if nome_novo is not None:
            perfil.nome = nome_novo
        if cor_nova is not None:
            perfil.cor = cor_nova
        perfil.save(update_fields=["nome", "cor"])
    return perfil_para_dict(usuario)


def trocar_senha(request, usuario, senha_atual: str, senha_nova: str) -> None:
    erros: dict[str, list[str]] = {}
    if not usuario.check_password(senha_atual):
        erros["senha_atual"] = ["A senha atual está incorreta."]
    try:
        validate_password(senha_nova, user=usuario)
    except ValidationError as erro:
        erros["senha_nova"] = list(erro.messages)
    if erros:
        raise ErroValidacao(erros)
    usuario.set_password(senha_nova)
    usuario.save(update_fields=["password"])
    # Mantém a sessão de quem trocou; as sessões de outros aparelhos deixam de valer (o hash da sessão muda).
    update_session_auth_hash(request, usuario)


# ---------- grupo ----------


def criar_grupo(usuario) -> dict:
    with transaction.atomic():
        perfil = Perfil.objects.select_for_update().filter(pk=usuario.pk).first()
        if perfil is None:
            raise ErroValidacao({"perfil": ["Informe seu nome e sua cor antes de criar o grupo."]})
        if perfil.grupo_id:
            raise ErroConflito("Você já pertence a um grupo.")
        grupo = Grupo.objects.create()
        perfil.grupo = grupo
        perfil.save(update_fields=["grupo"])
    return grupo_para_dict(grupo)


# ---------- convite ----------


def _hash(codigo: str) -> str:
    return hashlib.sha256(codigo.encode()).hexdigest()


def _pendente(convite: Convite) -> bool:
    return (
        convite.usado_em is None
        and convite.invalidado_em is None
        and convite.expira_em > timezone.now()
    )


def gerar_convite(usuario) -> tuple[str, object]:
    """Devolve o código (única vez em que ele existe em claro) e a validade."""
    perfil = _perfil_de(usuario)
    if perfil is None or not perfil.grupo_id:
        raise ErroConflito("Crie um grupo antes de convidar alguém.")
    with transaction.atomic():
        grupo = Grupo.objects.select_for_update().get(pk=perfil.grupo_id)
        if grupo.perfis.count() >= grupo.limite_membros:
            raise ErroConflito("O grupo já está completo.")
        agora = timezone.now()
        Convite.objects.filter(
            grupo=grupo, usado_em__isnull=True, invalidado_em__isnull=True
        ).update(invalidado_em=agora)
        codigo = secrets.token_urlsafe(32)  # 256 bits
        convite = Convite.objects.create(
            grupo=grupo,
            criado_por=perfil,
            codigo_hash=_hash(codigo),
            expira_em=agora + VALIDADE_DO_CONVITE,
        )
    return codigo, convite.expira_em


def aceitar_convite(request, codigo: str, nome: str, email: str, senha: str, cor: str):
    """Cria conta, perfil e entrada no grupo de uma vez. Toda falha de convite devolve a mesma resposta."""
    convite = Convite.objects.filter(codigo_hash=_hash(codigo or "")).first()
    if convite is None or not _pendente(convite):
        raise ErroGenerico(MENSAGEM_CONVITE)

    modelo = get_user_model()
    erros: dict[str, list[str]] = {}
    nome_ok = _juntar(erros, lambda: _nome_valido(nome))
    email_ok = _juntar(erros, lambda: _email_valido(email))
    cor_ok = _juntar(erros, lambda: _cor_valida(cor, _cores_dos_outros(convite.grupo_id)))
    _juntar(
        erros, lambda: _senha_valida(senha, modelo(username=email_ok or "", email=email_ok or ""))
    )
    if erros:
        raise ErroValidacao(erros)

    with transaction.atomic():
        # Ordem fixa das travas (grupo, depois convite), igual à de `gerar_convite`, para não travar em ciclo.
        grupo = Grupo.objects.select_for_update().get(pk=convite.grupo_id)
        convite = Convite.objects.select_for_update().get(pk=convite.pk)
        if not _pendente(convite) or grupo.perfis.count() >= grupo.limite_membros:
            raise ErroGenerico(MENSAGEM_CONVITE)
        if not all(
            domain.cores_distinguiveis(cor_ok, outra) for outra in _cores_dos_outros(grupo.pk)
        ):
            raise ErroValidacao(
                {"cor": ["Essa cor é igual ou parecida demais com a da outra pessoa do grupo."]}
            )
        try:
            with transaction.atomic():
                usuario = modelo.objects.create_user(
                    username=email_ok, email=email_ok, password=senha
                )
        except IntegrityError:
            # E-mail que já tem conta: a mesma resposta de qualquer convite inválido.
            raise ErroGenerico(MENSAGEM_CONVITE) from None
        Perfil.objects.create(usuario=usuario, nome=nome_ok, cor=cor_ok, grupo=grupo)
        convite.usado_em = timezone.now()
        convite.save(update_fields=["usado_em"])
    login(request, usuario, backend=BACKEND_PADRAO)
    return usuario
