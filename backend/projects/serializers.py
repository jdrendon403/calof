from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Assignment, Project

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    usuarios_asignados = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "nombre",
            "descripcion",
            "cliente",
            "estado",
            "fecha_inicio",
            "fecha_fin",
            "usuarios_asignados",
        )
        read_only_fields = ("id",)

    def get_usuarios_asignados(self, obj):
        return list(obj.asignaciones.values_list("usuario_id", flat=True))


class ProjectListSerializer(serializers.ModelSerializer):
    """Light serializer for list (no M2M detail)."""
    class Meta:
        model = Project
        fields = (
            "id",
            "nombre",
            "descripcion",
            "cliente",
            "estado",
            "fecha_inicio",
            "fecha_fin",
        )


class AssignmentSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)
    proyecto_nombre = serializers.CharField(source="proyecto.nombre", read_only=True)

    class Meta:
        model = Assignment
        fields = ("id", "usuario", "usuario_username", "proyecto", "proyecto_nombre", "fecha_programada")
        read_only_fields = ("id",)


class AssignUsersSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)

    def validate_user_ids(self, value):
        User = get_user_model()
        found = set(User.objects.filter(pk__in=value).values_list("pk", flat=True))
        missing = set(value) - found
        if missing:
            raise serializers.ValidationError(f"User IDs not found: {missing}")
        return value
