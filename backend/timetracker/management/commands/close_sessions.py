"""
Cierra registros de tiempo abiertos (hora_fin=null).
Uso: python manage.py close_sessions [--at 17:00|00:00]
Por defecto usa la hora actual como hora_fin.
"""
from django.utils import timezone
from django.core.management.base import BaseCommand

from timetracker.models import TimeEntry


class Command(BaseCommand):
    help = "Cierra registros de tiempo con hora_fin nula (cierre automático 17:00 / 00:00)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--at",
            type=str,
            default=None,
            help="Hora de cierre en formato HH:MM (ej. 17:00 o 00:00). Si no se indica, usa ahora.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo mostrar qué registros se cerrarían, sin modificar.",
        )

    def handle(self, *args, **options):
        at_str = options.get("at")
        dry_run = options.get("dry_run", False)

        qs = TimeEntry.objects.filter(hora_fin__isnull=True)
        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No hay registros abiertos."))
            return

        if at_str:
            from datetime import datetime
            try:
                hour, minute = map(int, at_str.split(":"))
                now = timezone.now()
                close_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if close_time > now:
                    close_time = close_time - timezone.timedelta(days=1)
            except (ValueError, TypeError):
                self.stderr.write(self.style.ERROR(f"Hora inválida: {at_str}. Use HH:MM."))
                return
        else:
            close_time = timezone.now()

        if dry_run:
            self.stdout.write(f"Se cerrarían {count} registro(s) con hora_fin={close_time}")
            for e in qs[:5]:
                self.stdout.write(f"  - {e.usuario} / {e.proyecto} desde {e.hora_inicio}")
            if count > 5:
                self.stdout.write(f"  ... y {count - 5} más")
            return

        updated = qs.update(hora_fin=close_time, cierre_automatico=True)
        self.stdout.write(self.style.SUCCESS(f"Cerrados {updated} registro(s) a las {close_time}."))
