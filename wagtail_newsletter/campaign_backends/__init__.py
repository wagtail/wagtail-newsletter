from django.conf import settings
from django.utils.module_loading import import_string


# TODO define a backend interface class


def get_backend():
    backend_class = import_string(
        getattr(
            settings,
            "WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND",
            "wagtail_newsletter.campaign_backends.mailchimp.MailchimpCampaignBackend",
        )
    )
    return backend_class()
