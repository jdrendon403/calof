from django.contrib import admin
from .models import TimeEntry


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("usuario", "proyecto", "hora_inicio", "hora_fin", "cierre_automatico")
    list_filter = ("proyecto", "cierre_automatico")
