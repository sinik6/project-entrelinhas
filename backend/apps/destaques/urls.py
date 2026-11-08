from django.urls import path

from . import views

urlpatterns = [
    path(
        "registros/<str:registro_id>/destaques",
        views.DestaquesDoRegistroView.as_view(),
        name="destaques-do-registro",
    ),
    path("destaques/<str:destaque_id>", views.DestaqueView.as_view(), name="destaque"),
    path(
        "destaques/<str:destaque_id>/comentarios",
        views.ComentariosView.as_view(),
        name="comentarios",
    ),
    path("comentarios/<str:comentario_id>", views.ComentarioView.as_view(), name="comentario"),
]
