# Generated manually for SGTP

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=200)),
                ("descripcion", models.TextField(blank=True)),
                ("cliente", models.CharField(blank=True, max_length=200)),
                ("estado", models.CharField(choices=[("ABIERTO", "Abierto"), ("CERRADO", "Cerrado")], default="ABIERTO", max_length=20)),
                ("fecha_inicio", models.DateField(blank=True, null=True)),
                ("fecha_fin", models.DateField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Proyecto",
                "verbose_name_plural": "Proyectos",
                "ordering": ["-fecha_inicio", "nombre"],
            },
        ),
        migrations.CreateModel(
            name="Assignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha_programada", models.DateField(blank=True, null=True)),
                ("proyecto", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="asignaciones", to="projects.project")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="asignaciones", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Asignación",
                "verbose_name_plural": "Asignaciones",
                "ordering": ["fecha_programada", "proyecto"],
                "unique_together": {("usuario", "proyecto")},
            },
        ),
        migrations.AddField(
            model_name="project",
            name="usuarios_asignados",
            field=models.ManyToManyField(blank=True, related_name="proyectos_asignados", through="projects.assignment", to=settings.AUTH_USER_MODEL),
        ),
    ]
