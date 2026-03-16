from django.urls import path
from . import views

urlpatterns = [
    path("start/", views.time_start),
    path("stop/", views.time_stop),
    path("current/", views.time_current),
    path("", views.time_list),
]
