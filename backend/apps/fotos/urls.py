from django.urls import path

from . import views

urlpatterns = [
    path("fotos", views.EnviarView.as_view(), name="fotos"),
    path("fotos/<str:foto_id>", views.FotoView.as_view(), name="foto"),
    path("fotos/<str:foto_id>/arquivo", views.ArquivoView.as_view(), name="foto-arquivo"),
    path("perfil/foto", views.PerfilFotoView.as_view(), name="perfil-foto"),
]
