# Generated by Django 5.2 on 2025-05-21 23:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("routes", "0004_alter_route_background"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GameBoard",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "title",
                    models.CharField(max_length=50, verbose_name="Nazwa planszy"),
                ),
                (
                    "rows",
                    models.PositiveSmallIntegerField(default=5, verbose_name="Wiersze"),
                ),
                (
                    "cols",
                    models.PositiveSmallIntegerField(default=5, verbose_name="Kolumny"),
                ),
                (
                    "dots",
                    models.JSONField(blank=True, default=list, verbose_name="Kropki"),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="boards",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-modified"],
            },
        ),
    ]
