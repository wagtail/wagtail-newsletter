import pytest

from wagtail_newsletter.campaign_backends import get_backend
from wagtail_newsletter.campaign_backends.mailchimp import MailchimpCampaignBackend

from ..conftest import MemoryCampaignBackend


@pytest.mark.parametrize(
    "dotted_path,cls",
    [
        (None, MailchimpCampaignBackend),
        ("tests.conftest.MemoryCampaignBackend", MemoryCampaignBackend),
    ],
)
def test_get_backend_lookup(settings, dotted_path, cls):
    settings.WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY = "mock key"
    if dotted_path is None:
        del settings.WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND
    else:
        settings.WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND = dotted_path

    assert type(get_backend()) is cls
