from django.urls import path

from . import views

urlpatterns = [
    path("", views.UsuarioListCreateView.as_view()),
    path("<int:pk>/", views.UsuarioDetailView.as_view()),
]
