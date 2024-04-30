from django.apps import AppConfig


class WagtailNewsletterDemoAppConfig(AppConfig):
    label = "demo"
    name = "demo"
    verbose_name = "Wagtail Newsletter demo"
    default_auto_field = "django.db.models.BigAutoField"
