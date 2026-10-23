import pytest
from django.db import OperationalError
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_responde_ok_sem_login():
    """001-C1: o health responde 200 sem autenticação."""
    resposta = APIClient().get("/api/v1/health")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


@pytest.mark.django_db
def test_health_consulta_o_banco(monkeypatch):
    """001-C2: banco fora do ar não devolve 200."""

    def falha(*args, **kwargs):
        raise OperationalError("banco fora do ar")

    monkeypatch.setattr("django.db.backends.utils.CursorWrapper.execute", falha)

    with pytest.raises(OperationalError):
        APIClient().get("/api/v1/health")
