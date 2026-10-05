from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"novedades", views.NovedadViewSet, basename="novedad")
router.register(r"insumos", views.SolicitudInsumoViewSet, basename="insumo")
router.register(r"informes", views.InformeServicioViewSet, basename="informe")
router.register(r"fotos", views.FotoViewSet, basename="foto")
router.register(r"notificaciones", views.NotificacionViewSet, basename="notificacion")

urlpatterns = [
    path("campo/proyectos/", views.mis_proyectos),
    path("archivos/<str:token>/", views.archivo, name="archivo"),
    path("", include(router.urls)),
]
