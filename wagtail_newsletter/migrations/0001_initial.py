# Generated by Django 5.0.4 on 2024-04-29 14:38

import django.core.serializers.json
import django.db.models.deletion

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("wagtailcore", "0089_log_entry_data_json_null_to_object"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NewsletterRecipients",
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
                ("name", models.CharField(max_length=1000)),
                ("audience", models.CharField(max_length=1000)),
                ("segment", models.CharField(blank=True, max_length=1000, null=True)),
            ],
            options={"verbose_name_plural": "Newsletter recipients"},
        ),
        migrations.CreateModel(
            name="NewsletterLogEntry",
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
                ("label", models.TextField()),
                ("action", models.CharField(blank=True, db_index=True, max_length=255)),
                (
                    "data",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(db_index=True, verbose_name="timestamp (UTC)"),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        blank=True,
                        editable=False,
                        help_text="Log entries that happened as part of the same user action are assigned the same UUID",
                        null=True,
                    ),
                ),
                ("content_changed", models.BooleanField(db_index=True, default=False)),
                ("deleted", models.BooleanField(default=False)),
                (
                    "content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="contenttypes.contenttype",
                        verbose_name="content type",
                    ),
                ),
                (
                    "page",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="wagtailcore.page",
                    ),
                ),
                (
                    "revision",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="wagtailcore.revision",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "newsletter log entry",
                "verbose_name_plural": "newsletter log entries",
                "ordering": ["-timestamp", "-id"],
            },
        ),
    ]
