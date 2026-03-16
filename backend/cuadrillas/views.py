from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from timetracker.serializers import TimeEntrySerializer
from users.models import Rol
from users.permissions import IsProjectLeader

from .models import Cuadrilla
from .serializers import CuadrillaSerializer
from .services import cuadrilla_current_status, cuadrilla_start, cuadrilla_stop


class CuadrillaViewSet(ModelViewSet):
    serializer_class = CuadrillaSerializer

    def get_queryset(self):
        user = self.request.user
        if user.rol == Rol.ADMIN:
            return Cuadrilla.objects.all().prefetch_related("miembros")
        if user.rol == Rol.LIDER:
            return Cuadrilla.objects.filter(lider=user).prefetch_related("miembros")
        return Cuadrilla.objects.filter(miembros=user, activa=True).prefetch_related("miembros")

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy",
                           "add_members", "remove_member"):
            return [IsAuthenticated(), IsProjectLeader()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(lider=self.request.user)

    def _is_cuadrilla_member(self, cuadrilla, user):
        if user.rol == Rol.ADMIN:
            return True
        if cuadrilla.lider == user:
            return True
        return cuadrilla.miembros.filter(pk=user.pk).exists()

    @action(detail=True, methods=["post"], url_path="add-members")
    def add_members(self, request, pk=None):
        cuadrilla = self.get_object()
        ids = request.data.get("user_ids", [])
        cuadrilla.miembros.add(*ids)
        return Response(CuadrillaSerializer(cuadrilla).data)

    @action(detail=True, methods=["post"], url_path="remove-member")
    def remove_member(self, request, pk=None):
        cuadrilla = self.get_object()
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"error": "user_id required"}, status=status.HTTP_400_BAD_REQUEST)
        cuadrilla.miembros.remove(user_id)
        return Response(CuadrillaSerializer(cuadrilla).data)

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        cuadrilla = self.get_object()
        if not self._is_cuadrilla_member(cuadrilla, request.user):
            return Response(
                {"error": "No pertenece a esta cuadrilla."},
                status=status.HTTP_403_FORBIDDEN,
            )
        result = cuadrilla_start(cuadrilla, triggered_by=request.user)
        return Response(
            {
                "entries": TimeEntrySerializer(result["entries"], many=True).data,
                "skipped_user_ids": result["skipped_user_ids"],
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="stop")
    def stop(self, request, pk=None):
        cuadrilla = self.get_object()
        if not self._is_cuadrilla_member(cuadrilla, request.user):
            return Response(
                {"error": "No pertenece a esta cuadrilla."},
                status=status.HTTP_403_FORBIDDEN,
            )
        result = cuadrilla_stop(cuadrilla)
        return Response({"entries": TimeEntrySerializer(result["entries"], many=True).data})

    @action(detail=True, methods=["get"], url_path="current")
    def current(self, request, pk=None):
        cuadrilla = self.get_object()
        result = cuadrilla_current_status(cuadrilla)
        return Response(
            {
                "active": result["active"],
                "entries": TimeEntrySerializer(result["entries"], many=True).data,
            }
        )
