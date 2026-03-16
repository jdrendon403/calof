from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from users.models import Usuario
from projects.models import Project, Assignment
from timetracker.models import TimeEntry


class SettlementCalculationTest(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username="u1",
            password="test123",
            rol="LIDER",
        )
        self.project = Project.objects.create(nombre="Proyecto", cliente="Cliente")
        Assignment.objects.create(usuario=self.user, proyecto=self.project)

    def test_settlement_agrupa_por_usuario(self):
        now = timezone.now()
        TimeEntry.objects.create(
            usuario=self.user,
            proyecto=self.project,
            hora_inicio=now - timedelta(hours=1),
            hora_fin=now,
        )
        TimeEntry.objects.create(
            usuario=self.user,
            proyecto=self.project,
            hora_inicio=now - timedelta(days=1, hours=2),
            hora_fin=now - timedelta(days=1),
        )
        from django.db.models import Sum, F, ExpressionWrapper, DurationField
        from reports.views import _parse_period
        start, end = _parse_period("month")
        base = TimeEntry.objects.filter(
            hora_inicio__gte=start,
            hora_inicio__lte=end,
        ).exclude(hora_fin__isnull=True).annotate(
            duration=ExpressionWrapper(F("hora_fin") - F("hora_inicio"), output_field=DurationField())
        )
        by_user = list(base.values("usuario_id").annotate(total_seconds=Sum("duration")))
        self.assertTrue(len(by_user) >= 1)
        total = by_user[0]["total_seconds"]
        self.assertIsNotNone(total)
        self.assertEqual(int(total.total_seconds() / 60), 180)  # 60 + 120 min
