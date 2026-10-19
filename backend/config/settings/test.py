"""Testes automatizados (pytest-django). Sempre em PostgreSQL real."""

from .base import *  # noqa: F403

DEBUG = False

# Hash rápido: os testes criam muitos usuários e o PBKDF2 real deixaria a suíte lenta.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Sem `collectstatic` nos testes: o WhiteNoise lê os estáticos sob demanda.
WHITENOISE_AUTOREFRESH = True
