from django.apps import AppConfig


class WagtailNewsletterTestAppConfig(AppConfig):
    label = "wagtail_newsletter_test"
    name = "wagtail_newsletter.test"
    verbose_name = "Wagtail Newsletter tests"
    default_auto_field = "django.db.models.AutoField"
