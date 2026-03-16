from rest_framework import serializers
from .models import TimeEntry


class TimeEntrySerializer(serializers.ModelSerializer):
    duracion_minutos = serializers.IntegerField(read_only=True)
    proyecto_nombre = serializers.CharField(source="proyecto.nombre", read_only=True)
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model = TimeEntry
        fields = (
            "id",
            "usuario",
            "usuario_username",
            "proyecto",
            "proyecto_nombre",
            "hora_inicio",
            "hora_fin",
            "duracion_minutos",
            "cierre_automatico",
            "cuadrilla",
        )
        read_only_fields = ("id", "hora_inicio", "hora_fin", "cierre_automatico")


class TimeStartSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()

    def validate_project_id(self, value):
        from projects.models import Project
        user = self.context["request"].user
        if not Project.objects.filter(pk=value, asignaciones__usuario=user).exists():
            raise serializers.ValidationError("No está asignado a este proyecto.")
        return value
