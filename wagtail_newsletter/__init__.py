from django.conf import settings


default_app_config = "wagtail_newsletter.apps.WagtailNewsletterAppConfig"


VERSION = (0, 2, 0)
__version__ = ".".join(map(str, VERSION))


DEFAULT_RECIPIENTS_MODEL = "wagtail_newsletter.NewsletterRecipients"


def get_recipients_model_string():
    return getattr(
        settings, "WAGTAIL_NEWSLETTER_RECIPIENTS_MODEL", DEFAULT_RECIPIENTS_MODEL
    )
