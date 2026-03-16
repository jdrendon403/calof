from django.utils import timezone
from celery import shared_task
from timetracker.models import TimeEntry


@shared_task
def close_open_sessions():
    """
    Cierra todos los registros con hora_fin=null usando el momento exacto de ejecución.
    Disparado por Celery Beat a las 17:00 y 00:00 hora Bogotá.
    """
    qs = TimeEntry.objects.filter(hora_fin__isnull=True)
    if not qs.exists():
        return 0
    return qs.update(hora_fin=timezone.now(), cierre_automatico=True)
