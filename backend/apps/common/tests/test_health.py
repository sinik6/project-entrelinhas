import pytest
from django.db import OperationalError
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_req_1_1_health_responde_ok_sem_login():
    """REQ-1.1: o health responde com sucesso e estado "ok" sem autenticação."""
    resposta = APIClient().get("/api/v1/health")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


@pytest.mark.django_db
def test_req_1_2_health_falha_quando_banco_nao_responde(monkeypatch):
    """REQ-1.2: banco que não aceita consulta não devolve 200 (fail-closed)."""

    def falha(*args, **kwargs):
        raise OperationalError("banco fora do ar")

    monkeypatch.setattr("django.db.backends.utils.CursorWrapper.execute", falha)

    with pytest.raises(OperationalError):
        APIClient().get("/api/v1/health")
