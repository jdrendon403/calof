from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TimeEntry
from .serializers import TimeEntrySerializer, TimeStartSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def time_start(request):
    """Inicia el contador para un proyecto. Un solo registro activo por usuario."""
    if TimeEntry.objects.filter(usuario=request.user, hora_fin__isnull=True).exists():
        return Response(
            {"error": "Ya tiene una actividad en curso. Finalícela primero."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    ser = TimeStartSerializer(data=request.data, context={"request": request})
    ser.is_valid(raise_exception=True)
    project_id = ser.validated_data["project_id"]
    from projects.models import Project
    project = Project.objects.get(pk=project_id)
    entry = TimeEntry.objects.create(
        usuario=request.user,
        proyecto=project,
        hora_inicio=timezone.now(),
    )
    return Response(TimeEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "POST"])
@permission_classes([IsAuthenticated])
def time_stop(request):
    """Finaliza la actividad actual del usuario."""
    entry = TimeEntry.objects.filter(usuario=request.user, hora_fin__isnull=True).first()
    if not entry:
        return Response(
            {"error": "No hay actividad en curso."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    entry.hora_fin = timezone.now()
    entry.save(update_fields=["hora_fin"])
    return Response(TimeEntrySerializer(entry).data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def time_current(request):
    """Devuelve el registro activo del usuario (para sincronizar el frontend)."""
    entry = TimeEntry.objects.filter(usuario=request.user, hora_fin__isnull=True).select_related("proyecto").first()
    if not entry:
        return Response({"active": False, "entry": None})
    return Response({"active": True, "entry": TimeEntrySerializer(entry).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def time_list(request):
    """Lista los registros de tiempo del usuario (o todos para Líder/Admin)."""
    from users.models import Rol
    if request.user.is_project_leader:
        qs = TimeEntry.objects.all().select_related("usuario", "proyecto").order_by("-hora_inicio")
    else:
        qs = TimeEntry.objects.filter(usuario=request.user).select_related("proyecto").order_by("-hora_inicio")
    serializer = TimeEntrySerializer(qs, many=True)
    return Response(serializer.data)
