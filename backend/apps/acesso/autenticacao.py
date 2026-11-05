"""Login por e-mail e sessão com CSRF obrigatório (spec 003, D-3 e D-4)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from rest_framework.authentication import SessionAuthentication


class BackendPorEmail(ModelBackend):
    """Autentica por e-mail e senha. O `ModelBackend` continua valendo para o Admin (nome de usuário)."""

    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return None
        modelo = get_user_model()
        usuario = modelo.objects.filter(email__iexact=email).first()
        if usuario is None:
            # Gasta o mesmo tempo de uma conta que existe, para o tempo não revelar o e-mail.
            modelo().set_password(password)
            return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None


class SessaoComCsrf(SessionAuthentication):
    """Sessão do Django que **sempre** confere o token de CSRF, inclusive para quem ainda não entrou.

    O `SessionAuthentication` do DRF só confere CSRF de quem já está autenticado, o que deixaria o login
    (e o aceite de convite) abertos a "login CSRF". Métodos seguros (GET) nunca são conferidos.
    """

    def authenticate(self, request):
        usuario = getattr(request._request, "user", None)
        self.enforce_csrf(request)
        if usuario is None or not usuario.is_authenticated or not usuario.is_active:
            return None
        return usuario, None

    def authenticate_header(self, request):
        # Sem isto o DRF responde 403 a quem não entrou; com isto responde 401, como o contrato diz.
        return "Session"
