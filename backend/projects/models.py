from django.db import models
from django.conf import settings


class EstadoProyecto(models.TextChoices):
    ABIERTO = "ABIERTO", "Abierto"
    CERRADO = "CERRADO", "Cerrado"


class Project(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    cliente = models.CharField(max_length=200, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoProyecto.choices,
        default=EstadoProyecto.ABIERTO,
    )
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    usuarios_asignados = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="proyectos_asignados",
        through="Assignment",
        blank=True,
    )

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ["-fecha_inicio", "nombre"]

    def __str__(self):
        return self.nombre


class Assignment(models.Model):
    """Planificación: usuario asignado a proyecto en una fecha."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="asignaciones",
    )
    proyecto = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="asignaciones",
    )
    fecha_programada = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Asignación"
        verbose_name_plural = "Asignaciones"
        ordering = ["fecha_programada", "proyecto"]
        unique_together = [["usuario", "proyecto"]]
