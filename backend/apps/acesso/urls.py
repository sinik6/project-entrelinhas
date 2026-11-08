from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf", views.CsrfView.as_view(), name="csrf"),
    path("auth/entrar", views.EntrarView.as_view(), name="entrar"),
    path("auth/recuperacao", views.RecuperacaoView.as_view(), name="recuperacao"),
    path("auth/redefinir", views.RedefinirView.as_view(), name="redefinir"),
    path("auth/sair", views.SairView.as_view(), name="sair"),
    path("perfil", views.PerfilView.as_view(), name="perfil"),
    path("perfil/senha", views.SenhaView.as_view(), name="perfil-senha"),
    path("grupo", views.GrupoView.as_view(), name="grupo"),
    path("grupo/convites", views.ConviteGerarView.as_view(), name="grupo-convites"),
    path("convites/aceitar", views.ConviteAceitarView.as_view(), name="convite-aceitar"),
]
