from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from users.models import Usuario
from projects.models import Project, Assignment
from timetracker.models import TimeEntry


class TimeEntryDurationTest(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username="operario1",
            password="testpass123",
            rol="OPERARIO",
        )
        self.project = Project.objects.create(nombre="Proyecto A", cliente="Cliente X")
        Assignment.objects.create(usuario=self.user, proyecto=self.project)

    def test_duracion_minutos_calculada(self):
        inicio = timezone.now() - timedelta(hours=2, minutes=30)
        fin = timezone.now()
        entry = TimeEntry.objects.create(
            usuario=self.user,
            proyecto=self.project,
            hora_inicio=inicio,
            hora_fin=fin,
        )
        self.assertEqual(entry.duracion_minutos, 150)

    def test_duracion_nula_si_sin_fin(self):
        entry = TimeEntry.objects.create(
            usuario=self.user,
            proyecto=self.project,
            hora_inicio=timezone.now(),
            hora_fin=None,
        )
        self.assertIsNone(entry.duracion_minutos)


class CloseSessionsCommandTest(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username="op2",
            password="testpass123",
            rol="OPERARIO",
        )
        self.project = Project.objects.create(nombre="P", cliente="C")
        Assignment.objects.create(usuario=self.user, proyecto=self.project)

    def test_close_sessions_cierra_abiertos(self):
        TimeEntry.objects.create(
            usuario=self.user,
            proyecto=self.project,
            hora_inicio=timezone.now() - timedelta(hours=1),
            hora_fin=None,
        )
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command("close_sessions", at="17:00", stdout=out)
        entry = TimeEntry.objects.get(usuario=self.user)
        self.assertIsNotNone(entry.hora_fin)
        self.assertTrue(entry.cierre_automatico)
