import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Cierre automático: 17:00 y 00:00 hora Bogotá
# Celery interpreta estas horas en CELERY_TIMEZONE = "America/Bogota"
app.conf.beat_schedule = {
    "close-sessions-5pm": {
        "task": "timetracker.tasks.close_open_sessions",
        "schedule": crontab(hour=17, minute=0),
    },
    "close-sessions-midnight": {
        "task": "timetracker.tasks.close_open_sessions",
        "schedule": crontab(hour=0, minute=0),
    },
}
