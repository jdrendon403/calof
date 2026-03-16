from django.contrib.auth.models import AbstractUser
from django.db import models


class Rol(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    LIDER = "LIDER", "Líder"
    OPERARIO = "OPERARIO", "Operario"


class Usuario(AbstractUser):
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.OPERARIO,
    )
    telefono = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_project_leader(self):
        return self.rol in (Rol.ADMIN, Rol.LIDER)
