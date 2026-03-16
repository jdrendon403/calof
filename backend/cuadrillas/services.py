from django.db import transaction
from django.utils import timezone

from timetracker.models import TimeEntry


def cuadrilla_start(cuadrilla, triggered_by):
    """
    Crea un TimeEntry para cada miembro de la cuadrilla con el mismo hora_inicio.
    Miembros con sesión individual activa se omiten y se reportan en skipped_user_ids.
    """
    now = timezone.now()
    miembros = list(cuadrilla.miembros.all())
    skipped = []
    created = []

    with transaction.atomic():
        for user in miembros:
            if TimeEntry.objects.filter(usuario=user, hora_fin__isnull=True).exists():
                skipped.append(user.pk)
                continue
            entry = TimeEntry.objects.create(
                usuario=user,
                proyecto=cuadrilla.proyecto,
                hora_inicio=now,
                cuadrilla=cuadrilla,
            )
            created.append(entry)

    return {"entries": created, "skipped_user_ids": skipped}


def cuadrilla_stop(cuadrilla):
    """
    Cierra todos los TimeEntry activos pertenecientes a esta cuadrilla.
    """
    now = timezone.now()
    with transaction.atomic():
        qs = TimeEntry.objects.filter(
            cuadrilla=cuadrilla, hora_fin__isnull=True
        ).select_related("usuario", "proyecto")
        entry_ids = list(qs.values_list("pk", flat=True))
        qs.update(hora_fin=now)
        entries = list(
            TimeEntry.objects.filter(pk__in=entry_ids).select_related("usuario", "proyecto")
        )
    return {"entries": entries}


def cuadrilla_current_status(cuadrilla):
    """
    Retorna las entradas activas de la cuadrilla y si está en curso o no.
    """
    entries = list(
        TimeEntry.objects.filter(
            cuadrilla=cuadrilla, hora_fin__isnull=True
        ).select_related("usuario", "proyecto")
    )
    return {"active": bool(entries), "entries": entries}
