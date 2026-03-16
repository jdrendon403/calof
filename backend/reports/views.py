"""
Reportes de liquidación: horas agregadas por usuario y proyecto.
"""
from django.db.models import Sum, F, ExpressionWrapper, DurationField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsProjectLeader
from timetracker.models import TimeEntry


def _parse_period(period):
    now = timezone.now()
    if period == "week":
        start = now - timezone.timedelta(days=7)
    else:
        start = now - timezone.timedelta(days=30)
    return start, now


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsProjectLeader])
def settlement(request):
    """
    Datos para liquidación: horas totales por usuario y por proyecto.
    Incluye entradas activas (hora_fin=null) usando el tiempo actual como cierre temporal.
    Query params: period=week|month (default month).
    """
    period = request.query_params.get("period", "month")
    start, end = _parse_period(period)

    base = TimeEntry.objects.filter(
        hora_inicio__gte=start,
        hora_inicio__lte=end,
    ).annotate(
        duration=ExpressionWrapper(
            Coalesce(F("hora_fin"), Value(end)) - F("hora_inicio"),
            output_field=DurationField(),
        )
    )

    by_user = base.values(
        "usuario__username", "usuario__first_name", "usuario__last_name", "usuario_id"
    ).annotate(total_seconds=Sum("duration"))
    user_list = []
    for row in by_user:
        total_seconds = row["total_seconds"].total_seconds() if row["total_seconds"] else 0
        first = row["usuario__first_name"]
        last = row["usuario__last_name"]
        nombre_completo = f"{first} {last}".strip() or row["usuario__username"]
        user_list.append({
            "usuario_id": row["usuario_id"],
            "username": row["usuario__username"],
            "nombre_completo": nombre_completo,
            "total_minutos": int(total_seconds / 60),
        })

    by_project = base.values("proyecto__nombre", "proyecto_id").annotate(
        total_seconds=Sum("duration")
    )
    project_list = []
    for row in by_project:
        total_seconds = row["total_seconds"].total_seconds() if row["total_seconds"] else 0
        project_list.append({
            "proyecto_id": row["proyecto_id"],
            "nombre": row["proyecto__nombre"],
            "total_minutos": int(total_seconds / 60),
        })

    return Response({
        "period": period,
        "desde": start.isoformat(),
        "hasta": end.isoformat(),
        "por_usuario": user_list,
        "por_proyecto": project_list,
    })
