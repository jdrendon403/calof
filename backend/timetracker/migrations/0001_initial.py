# Generated manually for SGTP

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("projects", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TimeEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hora_inicio", models.DateTimeField()),
                ("hora_fin", models.DateTimeField(blank=True, null=True)),
                ("cierre_automatico", models.BooleanField(default=False)),
                ("proyecto", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="registros_tiempo", to="projects.project")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="registros_tiempo", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Registro de tiempo",
                "verbose_name_plural": "Registros de tiempo",
                "ordering": ["-hora_inicio"],
            },
        ),
    ]
