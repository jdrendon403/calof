from django.contrib import admin

from .models import Foto, InformeServicio, Notificacion, Novedad, SolicitudInsumo


class FotoInline(admin.TabularInline):
    model = Foto
    extra = 0
    fields = ("archivo", "descripcion", "subido_por", "creada_en")
    readonly_fields = ("subido_por", "creada_en")


@admin.register(Novedad)
class NovedadAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "proyecto", "autor", "estado", "creada_en")
    list_filter = ("estado", "categoria", "proyecto")
    search_fields = ("titulo", "descripcion")
    inlines = [FotoInline]


@admin.register(SolicitudInsumo)
class SolicitudInsumoAdmin(admin.ModelAdmin):
    list_display = ("id", "proyecto", "autor", "estado", "fecha_requerida", "creada_en")
    list_filter = ("estado", "proyecto")
    search_fields = ("detalle",)
    inlines = [FotoInline]


@admin.register(InformeServicio)
class InformeServicioAdmin(admin.ModelAdmin):
    list_display = ("__str__", "proyecto", "fecha_servicio", "autor", "estado")
    list_filter = ("estado", "proyecto")
    search_fields = ("consecutivo", "actividades")
    filter_horizontal = ("participantes",)
    inlines = [FotoInline]


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ("destinatario", "tipo", "texto", "leida", "creada_en")
    list_filter = ("tipo", "leida")
