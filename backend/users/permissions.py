from rest_framework import permissions

from .models import Rol


class IsAdminUser(permissions.BasePermission):
    """Only admin users."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == Rol.ADMIN


class IsProjectLeader(permissions.BasePermission):
    """Admin or Líder."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_project_leader


class IsOperario(permissions.BasePermission):
    """Operario role (or above)."""

    def has_permission(self, request, view):
        return request.user.is_authenticated


class IsProjectLeaderOrReadOnly(permissions.BasePermission):
    """Operarios can read; only Líder/Admin can create/update/delete."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_project_leader
