from django.urls import path

from . import views

urlpatterns = [
    path("lembretes/chave-publica", views.ChavePublicaView.as_view(), name="lembretes-chave"),
    path("lembretes/assinaturas", views.AssinaturasView.as_view(), name="lembretes-assinaturas"),
]
