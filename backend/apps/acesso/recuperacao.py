"""Recuperação de senha por e-mail (spec 011, ADR-0013). Não importa DRF.

Pedido: a resposta é sempre a mesma, exista a conta ou não; o e-mail sai em segundo plano e o link usa só a base de
configuração (`APP_URL_BASE`), nunca dado do pedido. Redefinição: token do Django (HMAC sobre a conta, a senha e o último
login; vale `PASSWORD_RESET_TIMEOUT`), de uso único na prática (trocar a senha o invalida), com a mesma resposta para
qualquer link ruim. Nenhum log leva e-mail, token ou corpo de mensagem.
"""

import logging
import threading
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .erros import ErroGenerico, ErroValidacao
from .models import PedidoRecuperacao

log = logging.getLogger("apps.acesso")
MENSAGEM_PEDIDO = "Se este e-mail tiver conta, enviamos um link. Vale por 1 hora."
MENSAGEM_LINK_INVALIDO = "Link inválido ou vencido."
LIMITE_POR_HORA = 3
RETENCAO = timedelta(hours=24)
_threads: list[threading.Thread] = []


def agora():
    """O instante do pedido. É uma função para o teste poder fixar a hora."""
    return timezone.now()


def aguardar_envios() -> None:
    """Espera os e-mails em segundo plano (para os testes; o servidor nunca espera)."""
    for t in list(_threads):
        t.join(15)
    _threads.clear()


def _enviar_em_segundo_plano(destino: str, assunto: str, corpo: str) -> None:
    def tarefa():
        try:
            EmailMessage(assunto, corpo, to=[destino]).send(fail_silently=False)
        except Exception as erro:
            # Só o tipo do erro: a mensagem dele poderia trazer o e-mail, o corpo ou a senha do SMTP.
            log.error("envio do e-mail de recuperacao falhou tipo=%s", type(erro).__name__)

    t = threading.Thread(target=tarefa, daemon=True)
    _threads.append(t)
    t.start()


def _link(usuario) -> str:
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    # No fragmento (#): o token nunca vai ao servidor, a proxies nem a logs de acesso. Base só da configuração.
    return f"{settings.APP_URL_BASE.rstrip('/')}/#/redefinir/{uid}/{token}"


def _gastar_tempo() -> None:
    """Conta sem existência faz o mesmo número de consultas de uma que existe: o tempo não diferencia."""
    for _ in range(3):
        PedidoRecuperacao.objects.filter(usuario_id=0).count()


def pedir(email) -> None:
    """Sempre volta sem erro e sem dizer nada. Só envia a conta existente, ativa e dentro do limite por hora."""
    if not isinstance(email, str):
        return
    email = email.strip().lower()
    if not email or len(email) > 254:
        return
    try:
        validate_email(email)
    except ValidationError:
        return
    usuario = get_user_model().objects.filter(email__iexact=email, is_active=True).first()
    if usuario is None:
        _gastar_tempo()
        return
    instante = agora()
    with transaction.atomic():
        # Travar a conta serializa os pedidos dela: o limite de 3 vale também para pedidos simultâneos.
        get_user_model().objects.select_for_update().get(pk=usuario.pk)
        PedidoRecuperacao.objects.filter(
            usuario=usuario, criado_em__lt=instante - RETENCAO
        ).delete()
        recentes = PedidoRecuperacao.objects.filter(
            usuario=usuario, criado_em__gte=instante - timedelta(hours=1)
        ).count()
        if recentes >= LIMITE_POR_HORA:
            return
        PedidoRecuperacao.objects.create(usuario=usuario, criado_em=instante)
    corpo = (
        "Olá!\n\n"
        "Recebemos um pedido para redefinir a senha da sua conta no Entrelinhas. "
        "Abra o link abaixo para escolher uma senha nova. Ele vale por 1 hora e funciona uma vez só:\n\n"
        f"{_link(usuario)}\n\n"
        "Se não foi você, ignore esta mensagem: nada muda na sua conta.\n"
    )
    _enviar_em_segundo_plano(usuario.email, "Entrelinhas — redefinir senha", corpo)
    log.info("recuperacao pedida conta=%s", usuario.pk)


def _usuario_do_uid(uid):
    if not isinstance(uid, str) or not uid:
        return None
    try:
        pk = int(force_str(urlsafe_base64_decode(uid)))
        return get_user_model().objects.filter(pk=pk).first()
    except (TypeError, ValueError, OverflowError, UnicodeDecodeError):
        return None


def _encerrar_sessoes(usuario) -> None:
    for sessao in Session.objects.filter(expire_date__gt=timezone.now()):
        if sessao.get_decoded().get(SESSION_KEY) == str(usuario.pk):
            sessao.delete()


def redefinir(uid, token, nova_senha) -> None:
    """Uid ou token inválido, vencido ou já usado: a mesma resposta (400), sem alterar nada. Senha fraca: 422, e o token segue valendo."""
    usuario = _usuario_do_uid(uid)
    if (
        usuario is None
        or not usuario.is_active
        or not isinstance(token, str)
        or not default_token_generator.check_token(usuario, token)
    ):
        raise ErroGenerico(MENSAGEM_LINK_INVALIDO)
    if not isinstance(nova_senha, str):
        raise ErroValidacao({"nova_senha": ["Informe a senha nova."]})
    try:
        validate_password(nova_senha, user=usuario)
    except ValidationError as erro:
        raise ErroValidacao({"nova_senha": list(erro.messages)}) from None
    usuario.set_password(nova_senha)
    usuario.save(update_fields=["password"])
    _encerrar_sessoes(usuario)
    _enviar_em_segundo_plano(
        usuario.email,
        "Entrelinhas — sua senha foi alterada",
        "Olá!\n\nA senha da sua conta no Entrelinhas acabou de ser alterada. "
        "Se foi você, não precisa fazer nada. Se não foi, peça um novo link de recuperação "
        "agora e avise quem administra o app.\n",
    )
    log.info("senha redefinida conta=%s", usuario.pk)
