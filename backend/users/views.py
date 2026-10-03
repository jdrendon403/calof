from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Usuario
from .permissions import IsAdminUser, IsProjectLeader
from .throttles import LoginIPThrottle, LoginUsernameThrottle
from .serializers import (
    ChangePasswordSerializer,
    LoginResponseSerializer,
    UsuarioCreateSerializer,
    UsuarioSerializer,
)


def _login_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UsuarioSerializer(user).data,
        "rol": user.rol,
    }


class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT login; returns tokens + user + rol."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginUsernameThrottle, LoginIPThrottle]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = Usuario.objects.get(username=request.data["username"])
            data = _login_response(user)
            return Response(data, status=status.HTTP_200_OK)
        return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Current user profile."""
    return Response(UsuarioSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change the current user's password."""
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save(update_fields=["password"])
    return Response(status=status.HTTP_204_NO_CONTENT)


class UsuarioListCreateView(generics.ListCreateAPIView):
    queryset = Usuario.objects.all().order_by("username")

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated(), IsProjectLeader()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UsuarioCreateSerializer
        return UsuarioSerializer


class UsuarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
