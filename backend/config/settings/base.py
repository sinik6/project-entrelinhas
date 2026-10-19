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

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Prefixo público do Django na VPS: o domínio é dividido com outros sistemas e o Entrelinhas
# mora em /entrelinhas. Só o Admin e seus estáticos saem por ele; a API fica na rede interna
# e é chamada pelo BFF do front. Vazio no desenvolvimento: /admin/ e /static/ como sempre.
PREFIXO_URL = env("DJANGO_PREFIXO_URL", "").strip("/")
PREFIXO_ROTAS = f"{PREFIXO_URL}/" if PREFIXO_URL else ""

STATIC_URL = f"/{PREFIXO_URL}/django-static/" if PREFIXO_URL else "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
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
