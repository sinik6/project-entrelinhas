from django.urls import path

from . import views

urlpatterns = [
    path("registros", views.RegistrosView.as_view(), name="registros"),
    path("registros/<str:registro_id>", views.RegistroView.as_view(), name="registro"),
]
