from django.db import models
from django.conf import settings

from projects.models import Project


class TimeEntry(models.Model):
    """Registro de tiempo: inicio/fin de actividad por usuario y proyecto."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registros_tiempo",
    )
    proyecto = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="registros_tiempo",
    )
    hora_inicio = models.DateTimeField()
    hora_fin = models.DateTimeField(null=True, blank=True)
    cierre_automatico = models.BooleanField(default=False)
    cuadrilla = models.ForeignKey(
        "cuadrillas.Cuadrilla",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="registros_tiempo",
    )

    class Meta:
        verbose_name = "Registro de tiempo"
        verbose_name_plural = "Registros de tiempo"
        ordering = ["-hora_inicio"]

    def __str__(self):
        return f"{self.usuario} - {self.proyecto} ({self.hora_inicio})"

    @property
    def duracion_minutos(self):
        if self.hora_fin is None:
            return None
        delta = self.hora_fin - self.hora_inicio
        return int(delta.total_seconds() / 60)
