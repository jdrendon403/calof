import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


def _ruta(carpeta, ext):
    """Nombre aleatorio para que la ruta no revele datos ni se pueda adivinar."""
    return f"{carpeta}/{timezone.now():%Y/%m}/{uuid.uuid4().hex}.{ext}"


def ruta_foto(instance, filename):
    return _ruta("fotos", "jpg")


def ruta_miniatura(instance, filename):
    return _ruta("fotos/miniaturas", "jpg")


def ruta_firma(instance, filename):
    return _ruta("informes/firmas", "png")


def ruta_pdf(instance, filename):
    return _ruta("informes/pdf", "pdf")


class CategoriaNovedad(models.TextChoices):
    SEGURIDAD = "SEGURIDAD", "Seguridad"
    DANO_FALLA = "DANO_FALLA", "Daño o falla"
    RETRASO = "RETRASO", "Retraso o bloqueo"
    PERSONAL = "PERSONAL", "Personal"
    OTRA = "OTRA", "Otra"


class EstadoNovedad(models.TextChoices):
    ABIERTA = "ABIERTA", "Abierta"
    ATENDIDA = "ATENDIDA", "Atendida"


class Novedad(models.Model):
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="novedades"
    )
    # Opcional: una novedad de personal (ausencia, incapacidad) puede no tener proyecto.
    proyecto = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.SET_NULL, related_name="novedades"
    )
    categoria = models.CharField(max_length=20, choices=CategoriaNovedad.choices, default=CategoriaNovedad.OTRA)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_hecho = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=EstadoNovedad.choices, default=EstadoNovedad.ABIERTA)
    respuesta = models.TextField(blank=True)
    atendida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    atendida_en = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Novedad"
        verbose_name_plural = "Novedades"
        ordering = ["-creada_en"]

    def __str__(self):
        return self.titulo


class EstadoSolicitud(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    APROBADA = "APROBADA", "Aprobada"
    RECHAZADA = "RECHAZADA", "Rechazada"
    ENTREGADA = "ENTREGADA", "Entregada"


class SolicitudInsumo(models.Model):
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="solicitudes_insumo"
    )
    proyecto = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="solicitudes_insumo"
    )
    detalle = models.TextField(help_text="Qué se necesita y en qué cantidad (texto libre).")
    fecha_requerida = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=EstadoSolicitud.choices, default=EstadoSolicitud.PENDIENTE)
    comentario = models.TextField(blank=True)
    gestionada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    gestionada_en = models.DateTimeField(null=True, blank=True)
    entregada_en = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Solicitud de insumos"
        verbose_name_plural = "Solicitudes de insumos"
        ordering = ["-creada_en"]

    def __str__(self):
        return f"Solicitud #{self.pk} — {self.proyecto}"


class EstadoInforme(models.TextChoices):
    BORRADOR = "BORRADOR", "Borrador"
    ENVIADO = "ENVIADO", "Enviado"
    APROBADO = "APROBADO", "Aprobado"
    DEVUELTO = "DEVUELTO", "Devuelto"


class InformeServicio(models.Model):
    # Se asigna al aprobar: INF-2026-0001
    consecutivo = models.CharField(max_length=20, unique=True, null=True, blank=True)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="informes"
    )
    proyecto = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="informes"
    )
    fecha_servicio = models.DateField(default=timezone.localdate)
    ubicacion = models.CharField(max_length=300, blank=True)
    actividades = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="informes_participados"
    )
    firma_nombre = models.CharField(max_length=200, blank=True)
    firma_cargo = models.CharField(max_length=200, blank=True)
    firma_imagen = models.ImageField(upload_to=ruta_firma, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=EstadoInforme.choices, default=EstadoInforme.BORRADOR)
    comentario_revision = models.TextField(blank=True)
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    revisado_en = models.DateTimeField(null=True, blank=True)
    enviado_en = models.DateTimeField(null=True, blank=True)
    pdf = models.FileField(upload_to=ruta_pdf, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Informe de servicio"
        verbose_name_plural = "Informes de servicio"
        ordering = ["-fecha_servicio", "-creado_en"]

    def __str__(self):
        return self.consecutivo or f"Informe #{self.pk} (sin aprobar)"


class Foto(models.Model):
    """Foto adjunta a exactamente uno de: novedad, solicitud de insumos o informe."""
    archivo = models.ImageField(upload_to=ruta_foto)
    miniatura = models.ImageField(upload_to=ruta_miniatura)
    descripcion = models.CharField(max_length=300, blank=True)
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    novedad = models.ForeignKey(Novedad, null=True, blank=True, on_delete=models.CASCADE, related_name="fotos")
    solicitud = models.ForeignKey(
        SolicitudInsumo, null=True, blank=True, on_delete=models.CASCADE, related_name="fotos"
    )
    informe = models.ForeignKey(
        InformeServicio, null=True, blank=True, on_delete=models.CASCADE, related_name="fotos"
    )

    class Meta:
        verbose_name = "Foto"
        verbose_name_plural = "Fotos"
        ordering = ["creada_en"]
        constraints = [
            models.CheckConstraint(
                name="foto_un_solo_padre",
                check=(
                    Q(novedad__isnull=False, solicitud__isnull=True, informe__isnull=True)
                    | Q(novedad__isnull=True, solicitud__isnull=False, informe__isnull=True)
                    | Q(novedad__isnull=True, solicitud__isnull=True, informe__isnull=False)
                ),
            )
        ]

    @property
    def padre(self):
        return self.novedad or self.solicitud or self.informe


class TipoNotificacion(models.TextChoices):
    NOVEDAD = "NOVEDAD", "Novedad"
    INSUMO = "INSUMO", "Insumos"
    INFORME = "INFORME", "Informe"


class Notificacion(models.Model):
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificaciones"
    )
    tipo = models.CharField(max_length=20, choices=TipoNotificacion.choices)
    texto = models.CharField(max_length=300)
    enlace = models.CharField(max_length=200, blank=True)
    leida = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-creada_en"]
        indexes = [models.Index(fields=["destinatario", "leida"])]

    def __str__(self):
        return self.texto
