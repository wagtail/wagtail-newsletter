from unittest.mock import Mock

import pytest

from django.core.exceptions import ImproperlyConfigured
from mailchimp_marketing.api_client import ApiClientError

from wagtail_newsletter.campaign_backends.mailchimp import (
    AudienceNotFoundError,
    MailchimpAudience,
    MailchimpAudienceSegment,
    MailchimpCampaignBackend,
)


class MockMailchimpCampaignBackend(MailchimpCampaignBackend):
    def __init__(self):
        self.client = Mock()


@pytest.fixture
def backend():
    return MockMailchimpCampaignBackend()


def test_no_api_key(settings):
    settings.WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY = None
    with pytest.raises(ImproperlyConfigured) as error:
        MailchimpCampaignBackend()

    assert error.match(r"WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY is not set")


def test_get_audiences(backend: MockMailchimpCampaignBackend):
    backend.client.lists.get_all_lists.return_value = {
        "lists": [
            {"id": "be13e6ca91", "name": "Torchbox", "stats": {"member_count": 8}},
            {"id": "9af08f2afa", "name": "Other", "stats": {"member_count": 13}},
        ],
    }

    assert backend.get_audiences() == [
        MailchimpAudience(id="be13e6ca91", name="Torchbox", member_count=8),
        MailchimpAudience(id="9af08f2afa", name="Other", member_count=13),
    ]


def test_get_audience_segments(backend: MockMailchimpCampaignBackend):
    backend.client.lists.list_segments.return_value = {
        "list_id": "be13e6ca91",
        "segments": [
            {"id": 2103836, "member_count": 3, "name": "Membership"},
            {"id": 2103837, "member_count": 1, "name": "Personal"},
            {"id": 2103838, "member_count": 1, "name": "Sponsors"},
        ],
    }

    assert backend.get_audience_segments("be13e6ca91") == [
        MailchimpAudienceSegment(
            id="be13e6ca91/2103836", name="Membership", member_count=3
        ),
        MailchimpAudienceSegment(
            id="be13e6ca91/2103837", name="Personal", member_count=1
        ),
        MailchimpAudienceSegment(
            id="be13e6ca91/2103838", name="Sponsors", member_count=1
        ),
    ]


def test_get_audience_segments_list_not_found(backend: MockMailchimpCampaignBackend):
    backend.client.lists.list_segments.side_effect = ApiClientError("", 404)

    with pytest.raises(AudienceNotFoundError):
        backend.get_audience_segments("be13e6ca91")
