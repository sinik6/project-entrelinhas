import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_responde_ok_sem_login():
    resposta = APIClient().get("/api/v1/health")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"
