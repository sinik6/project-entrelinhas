from django.urls import path

from . import views

urlpatterns = [path("calendario", views.CalendarioView.as_view(), name="calendario")]
