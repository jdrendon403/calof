from django.conf import settings
from django.db import models


class Cuadrilla(models.Model):
    nombre = models.CharField(max_length=200)
    proyecto = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="cuadrillas",
    )
    lider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cuadrillas_lideradas",
    )
    miembros = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="cuadrillas",
        blank=True,
    )
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cuadrilla"
        verbose_name_plural = "Cuadrillas"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.nombre} — {self.proyecto.nombre}"
