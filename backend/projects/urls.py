from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet, AssignmentViewSet

router = DefaultRouter()
router.register(r"", ProjectViewSet, basename="project")
router.register(r"assignments", AssignmentViewSet, basename="assignment")

urlpatterns = [
    path("", include(router.urls)),
]
