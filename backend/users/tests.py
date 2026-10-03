from django.core.cache import cache
from django.test import TestCase, override_settings
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


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class PasswordTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.admin = Usuario.objects.create_user(username="admin", password="admin123", rol="ADMIN")
        self.operario = Usuario.objects.create_user(username="operario", password="op123", rol="OPERARIO")

    def test_create_user_accepts_4_chars(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/users/", {"username": "nuevo", "password": "1234", "rol": "OPERARIO"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Usuario.objects.get(username="nuevo").check_password("1234"))

    def test_create_user_rejects_3_chars(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/users/", {"username": "nuevo", "password": "123", "rol": "OPERARIO"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_admin_can_set_password_on_update(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f"/api/users/{self.operario.id}/", {"password": "nueva"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.operario.refresh_from_db()
        self.assertTrue(self.operario.check_password("nueva"))

    def test_update_without_password_keeps_it(self):
        self.client.force_authenticate(user=self.admin)
        self.client.patch(f"/api/users/{self.operario.id}/", {"telefono": "123"})
        self.operario.refresh_from_db()
        self.assertTrue(self.operario.check_password("op123"))

    def test_change_own_password(self):
        self.client.force_authenticate(user=self.operario)
        response = self.client.post(
            "/api/auth/change-password/", {"current_password": "op123", "new_password": "abcd"}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.operario.refresh_from_db()
        self.assertTrue(self.operario.check_password("abcd"))

    def test_change_password_wrong_current(self):
        self.client.force_authenticate(user=self.operario)
        response = self.client.post(
            "/api/auth/change-password/", {"current_password": "mala", "new_password": "abcd"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_password", response.data)
        self.operario.refresh_from_db()
        self.assertTrue(self.operario.check_password("op123"))

    def test_change_password_too_short(self):
        self.client.force_authenticate(user=self.operario)
        response = self.client.post(
            "/api/auth/change-password/", {"current_password": "op123", "new_password": "abc"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

    def test_change_password_requires_auth(self):
        response = self.client.post(
            "/api/auth/change-password/", {"current_password": "op123", "new_password": "abcd"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_throttled_per_username(self):
        for _ in range(5):
            response = self.client.post("/api/auth/login/", {"username": "operario", "password": "mala"})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post("/api/auth/login/", {"username": "operario", "password": "op123"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        # Otro usuario desde la misma IP no queda bloqueado
        response = self.client.post("/api/auth/login/", {"username": "admin", "password": "admin123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
