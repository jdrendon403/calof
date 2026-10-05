from django.contrib.auth import get_user_model
from rest_framework import serializers

from .archivos import url_firmada
from .models import Foto, InformeServicio, Notificacion, Novedad, SolicitudInsumo
from .services import nombre, proyectos_permitidos, puede_gestionar

User = get_user_model()


class FotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    miniatura_url = serializers.SerializerMethodField()

    class Meta:
        model = Foto
        fields = ("id", "descripcion", "url", "miniatura_url", "creada_en")

    def get_url(self, obj):
        return url_firmada(obj.archivo)

    def get_miniatura_url(self, obj):
        return url_firmada(obj.miniatura)


class BaseCampoSerializer(serializers.ModelSerializer):
    """Campos comunes: autor, nombre del proyecto, fotos y validación del proyecto."""
    autor_nombre = serializers.SerializerMethodField()
    proyecto_nombre = serializers.CharField(source="proyecto.nombre", read_only=True, default=None)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    fotos = FotoSerializer(many=True, read_only=True)
    puede_gestionar = serializers.SerializerMethodField()

    def get_autor_nombre(self, obj):
        return nombre(obj.autor)

    def get_puede_gestionar(self, obj):
        request = self.context.get("request")
        return bool(request) and puede_gestionar(request.user, obj)

    def validate_proyecto(self, value):
        if value is None:
            return value
        user = self.context["request"].user
        if not proyectos_permitidos(user).filter(pk=value.pk).exists():
            raise serializers.ValidationError("No tiene acceso a este proyecto.")
        return value


class NovedadSerializer(BaseCampoSerializer):
    categoria_display = serializers.CharField(source="get_categoria_display", read_only=True)
    atendida_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Novedad
        fields = (
            "id", "autor", "autor_nombre", "proyecto", "proyecto_nombre", "categoria", "categoria_display",
            "titulo", "descripcion", "fecha_hecho", "estado", "estado_display", "respuesta",
            "atendida_por_nombre", "atendida_en", "creada_en", "fotos", "puede_gestionar",
        )
        read_only_fields = ("autor", "estado", "respuesta", "atendida_en", "creada_en")

    def get_atendida_por_nombre(self, obj):
        return nombre(obj.atendida_por) if obj.atendida_por_id else None


class SolicitudInsumoSerializer(BaseCampoSerializer):
    gestionada_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudInsumo
        fields = (
            "id", "autor", "autor_nombre", "proyecto", "proyecto_nombre", "detalle", "fecha_requerida",
            "estado", "estado_display", "comentario", "gestionada_por_nombre", "gestionada_en",
            "entregada_en", "creada_en", "fotos", "puede_gestionar",
        )
        read_only_fields = ("autor", "estado", "comentario", "gestionada_en", "entregada_en", "creada_en")

    def get_gestionada_por_nombre(self, obj):
        return nombre(obj.gestionada_por) if obj.gestionada_por_id else None


class ParticipanteSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "nombre")

    def get_nombre(self, obj):
        return nombre(obj)


class InformeServicioSerializer(BaseCampoSerializer):
    participantes = ParticipanteSerializer(many=True, read_only=True)
    participante_ids = serializers.PrimaryKeyRelatedField(
        source="participantes", queryset=User.objects.all(), many=True, write_only=True, required=False
    )
    cliente = serializers.CharField(source="proyecto.cliente", read_only=True)
    firma_url = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()
    revisado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = InformeServicio
        fields = (
            "id", "consecutivo", "autor", "autor_nombre", "proyecto", "proyecto_nombre", "cliente",
            "fecha_servicio", "ubicacion", "actividades", "observaciones", "participantes", "participante_ids",
            "firma_nombre", "firma_cargo", "firma_url", "estado", "estado_display", "comentario_revision",
            "revisado_por_nombre", "revisado_en", "enviado_en", "pdf_url", "creado_en", "actualizado_en",
            "fotos", "puede_gestionar",
        )
        read_only_fields = (
            "consecutivo", "autor", "estado", "comentario_revision", "revisado_en", "enviado_en",
            "creado_en", "actualizado_en",
        )

    def get_firma_url(self, obj):
        return url_firmada(obj.firma_imagen)

    def get_pdf_url(self, obj):
        url = url_firmada(obj.pdf)
        return f"{url}?nombre={obj.consecutivo}.pdf" if url else None

    def get_revisado_por_nombre(self, obj):
        return nombre(obj.revisado_por) if obj.revisado_por_id else None


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ("id", "tipo", "texto", "enlace", "leida", "creada_en")
