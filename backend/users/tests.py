from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from users.models import Usuario


class PermissionsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = Usuario.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="admin123",
            rol="ADMIN",
        )
        self.operario = Usuario.objects.create_user(
            username="operario",
            password="op123",
            rol="OPERARIO",
        )

    def test_operario_cannot_access_users_list(self):
        self.client.force_authenticate(user=self.operario)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_users_list(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_access_users(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
