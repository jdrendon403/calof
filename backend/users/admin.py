from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ("username", "email", "rol", "telefono", "is_staff")
    list_filter = ("rol", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("SGTP", {"fields": ("rol", "telefono")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("SGTP", {"fields": ("rol", "telefono")}),
    )
