from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Rol, Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    # Opcional: el admin puede asignar una contraseña nueva al editar un usuario
    password = serializers.CharField(write_only=True, required=False)

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
            "password",
        )
        read_only_fields = ("id", "username")

    def validate_password(self, value):
        validate_password(value, self.instance)
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

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

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = Usuario.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UsuarioSerializer()
    rol = serializers.ChoiceField(choices=Rol.choices)
