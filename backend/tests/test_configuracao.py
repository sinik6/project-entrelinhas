import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def test_req_2_1_producao_recusa_subir_sem_secret_key():
    """REQ-2.1 / CTL-3: settings de produção sem DJANGO_SECRET_KEY é erro de configuração."""
    ambiente = {k: v for k, v in os.environ.items() if k != "DJANGO_SECRET_KEY"}
    ambiente["DJANGO_ALLOWED_HOSTS"] = "localhost"

    resultado = subprocess.run(
        [sys.executable, "-c", "import config.settings.prod"],
        cwd=BACKEND,
        env=ambiente,
        capture_output=True,
        text=True,
    )

    assert resultado.returncode != 0
    assert "DJANGO_SECRET_KEY" in resultado.stderr


def test_nfr_sec_2_producao_usa_hasher_forte_por_padrao():
    """[002] NFR-SEC-2 / CTL-5: as settings de produção usam PBKDF2 (só os testes usam MD5)."""
    resultado = subprocess.run(
        [
            sys.executable,
            "-c",
            "from django.conf import settings; print(settings.PASSWORD_HASHERS[0])",
        ],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "config.settings.prod",
            "DJANGO_SECRET_KEY": "x" * 60,
            "DJANGO_ALLOWED_HOSTS": "localhost",
        },
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip().endswith("PBKDF2PasswordHasher")
