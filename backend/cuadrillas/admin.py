from django.contrib import admin

from .models import Cuadrilla


@admin.register(Cuadrilla)
class CuadrillaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "proyecto", "lider", "activa", "fecha_creacion")
    list_filter = ("activa", "proyecto")
    filter_horizontal = ("miembros",)
