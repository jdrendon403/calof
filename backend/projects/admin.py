from django.contrib import admin
from .models import Assignment, Project


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("nombre", "cliente", "estado", "fecha_inicio", "fecha_fin")
    list_filter = ("estado",)
    search_fields = ("nombre", "cliente")
    inlines = [AssignmentInline]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("usuario", "proyecto", "fecha_programada")
    list_filter = ("proyecto",)
