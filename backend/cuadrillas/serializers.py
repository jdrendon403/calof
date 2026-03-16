from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Cuadrilla

User = get_user_model()


class CuadrillaMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")


class CuadrillaSerializer(serializers.ModelSerializer):
    miembros = CuadrillaMemberSerializer(many=True, read_only=True)
    miembro_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    proyecto_nombre = serializers.CharField(source="proyecto.nombre", read_only=True)
    lider_username = serializers.CharField(source="lider.username", read_only=True)

    class Meta:
        model = Cuadrilla
        fields = (
            "id", "nombre", "proyecto", "proyecto_nombre",
            "lider", "lider_username", "miembros", "miembro_ids",
            "activa", "fecha_creacion",
        )
        read_only_fields = ("id", "fecha_creacion", "lider")

    def create(self, validated_data):
        miembro_ids = validated_data.pop("miembro_ids", [])
        cuadrilla = Cuadrilla.objects.create(**validated_data)
        if miembro_ids:
            cuadrilla.miembros.set(miembro_ids)
        return cuadrilla

    def update(self, instance, validated_data):
        miembro_ids = validated_data.pop("miembro_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if miembro_ids is not None:
            instance.miembros.set(miembro_ids)
        return instance
