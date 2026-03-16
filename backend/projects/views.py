from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from users.models import Rol
from users.permissions import IsProjectLeader, IsProjectLeaderOrReadOnly

from .models import Assignment, Project
from .serializers import AssignmentSerializer, AssignUsersSerializer, ProjectSerializer


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectLeaderOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.rol == Rol.OPERARIO:
            return Project.objects.filter(usuarios_asignados=user).distinct()
        return Project.objects.all()

    @action(detail=True, methods=["post"], url_path="assign-users")
    def assign_users(self, request, pk=None):
        project = self.get_object()
        ser = AssignUsersSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        for uid in ser.validated_data["user_ids"]:
            Assignment.objects.get_or_create(proyecto=project, usuario_id=uid)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="unassign-user")
    def unassign_user(self, request, pk=None):
        project = self.get_object()
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"error": "user_id required"}, status=status.HTTP_400_BAD_REQUEST)
        Assignment.objects.filter(proyecto=project, usuario_id=user_id).delete()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class AssignmentViewSet(ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [IsProjectLeader]

    def get_queryset(self):
        return Assignment.objects.select_related("usuario", "proyecto").all()

    def get_queryset_filtered_by_project(self):
        project_id = self.kwargs.get("project_pk")
        return self.get_queryset().filter(proyecto_id=project_id)
