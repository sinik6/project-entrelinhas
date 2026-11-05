"""Configuração comum a todos os ambientes.

Valores sensíveis ou dependentes do ambiente vêm de variáveis de ambiente. Os arquivos
`dev.py`, `test.py` e `prod.py` importam daqui e ajustam só o que muda.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

VERSAO_API = "0.1.0"


def env(nome: str, padrao: str | None = None) -> str:
    """Lê variável de ambiente; sem padrão, a ausência é erro de configuração."""
    valor = os.environ.get(nome, padrao)
    if valor is None:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {nome}")
    return valor


def env_lista(nome: str, padrao: str = "") -> list[str]:
    return [item.strip() for item in env(nome, padrao).split(",") if item.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-inseguro-troque-em-producao-0123456789abcdef")
DEBUG = False
ALLOWED_HOSTS = env_lista("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    # Domínios do Entrelinhas (um app por domínio).
    "apps.common",
    "apps.acesso",
    "apps.fotos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "entrelinhas"),
        "USER": env("POSTGRES_USER", "entrelinhas"),
        "PASSWORD": env("POSTGRES_PASSWORD", "entrelinhas"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        # Cada request é uma transação: erro no meio desfaz tudo.
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login por e-mail (spec 003): o ModelBackend continua valendo para o Admin, que entra por nome de usuário.
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "apps.acesso.autenticacao.BackendPorEmail",
]

# Política de senhas (spec 002, D-2): vale para o Admin, para o comando `administrador_inicial` e
# para as contas das próximas mudanças. O padrão do Django é uma lista vazia, ou seja, sem política.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Prefixo público do Django na VPS: o domínio é dividido com outros sistemas e o Entrelinhas
# mora em /entrelinhas. Só o Admin e seus estáticos saem por ele; a API fica na rede interna
# e é chamada pelo BFF do front. Vazio no desenvolvimento: /admin/ e /static/ como sempre.
PREFIXO_URL = env("DJANGO_PREFIXO_URL", "").strip("/")
PREFIXO_ROTAS = f"{PREFIXO_URL}/" if PREFIXO_URL else ""

# Cookies com nome e caminho próprios: a VPS divide o domínio com outros sistemas (ADR-0006).
# O cookie de CSRF também é HttpOnly: o app recebe o token no corpo de /auth/csrf, não o lê do cookie.
SESSION_COOKIE_NAME = "entrelinhas_sessionid"
CSRF_COOKIE_NAME = "entrelinhas_csrftoken"
SESSION_COOKIE_PATH = f"/{PREFIXO_URL}/" if PREFIXO_URL else "/"
CSRF_COOKIE_PATH = SESSION_COOKIE_PATH
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

STATIC_URL = f"/{PREFIXO_URL}/django-static/" if PREFIXO_URL else "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Fotos privadas (spec 004): fora de static e media, num volume só da API; servidas por endpoint autenticado.
FOTOS_DIR = Path(env("FOTOS_DIR", str(BASE_DIR / "fotos_dados")))

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.acesso.autenticacao.SessaoComCsrf"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "texto": {
            "format": "%(asctime)s %(levelname)-7s %(name)s %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "texto"}},
    "root": {"handlers": ["console"], "level": env("LOG_NIVEL", "INFO")},
    "loggers": {
        "django.server": {"level": "WARNING"},
        "django.request": {"level": "ERROR"},
    },
}
