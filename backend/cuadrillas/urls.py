from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CuadrillaViewSet

router = DefaultRouter()
router.register(r"", CuadrillaViewSet, basename="cuadrilla")

urlpatterns = [path("", include(router.urls))]
