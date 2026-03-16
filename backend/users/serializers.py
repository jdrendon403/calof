from rest_framework import serializers

from .models import Rol, Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "rol",
            "telefono",
            "is_active",
        )
        read_only_fields = ("id", "username")


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = (
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "rol",
            "telefono",
        )

    def create(self, validated_data):
        user = Usuario.objects.create_user(**validated_data)
        return user


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UsuarioSerializer()
    rol = serializers.ChoiceField(choices=Rol.choices)
