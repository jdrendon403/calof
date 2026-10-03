"""
URL configuration for SGTP project.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenRefreshView

from users import views
from users.views import CustomTokenObtainPairView
from reports import views as reports_views

spectacular_view = SpectacularAPIView.as_view()
spectacular_redoc_view = SpectacularRedocView.as_view(url_name="schema")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/me/", views.me),
    path("api/auth/change-password/", views.change_password),
    path("api/users/", include("users.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/time/", include("timetracker.urls")),
    path("api/reports/settlement/", reports_views.settlement),
    path("api/cuadrillas/", include("cuadrillas.urls")),
    path("api/schema/", spectacular_view, name="schema"),
    path("api/docs/", spectacular_redoc_view),
]
