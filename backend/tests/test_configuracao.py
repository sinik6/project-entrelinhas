import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def test_producao_recusa_subir_sem_secret_key():
    """001-C5: settings de produção sem DJANGO_SECRET_KEY é erro de configuração."""
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
