from unittest.mock import Mock

import pytest

from django.core.exceptions import ImproperlyConfigured
from mailchimp_marketing.api_client import ApiClientError

from wagtail_newsletter.audiences import (
    Audience,
    AudienceSegment,
)
from wagtail_newsletter.campaign_backends import CampaignBackend, get_backend
from wagtail_newsletter.campaign_backends.mailchimp import MailchimpCampaignBackend


class MockMailchimpCampaignBackend(MailchimpCampaignBackend):
    def __init__(self):
        self.client = Mock()


class CustomCampaignBackend(CampaignBackend):
    def get_audiences(self):
        raise NotImplementedError

    def get_audience_segments(self, audience_id):
        raise NotImplementedError


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
        Audience(id="be13e6ca91", name="Torchbox", member_count=8),
        Audience(id="9af08f2afa", name="Other", member_count=13),
    ]


def test_get_audience_segments(backend: MockMailchimpCampaignBackend):
    backend.client.lists.list_segments.return_value = {
        "list_id": "be13e6ca91",
        "segments": [
            {"id": 2103836, "member_count": 3, "name": "Segment One"},
            {"id": 2103837, "member_count": 1, "name": "Segment Two"},
            {"id": 2103838, "member_count": 1, "name": "Segment Three"},
        ],
    }

    assert backend.get_audience_segments("be13e6ca91") == [
        AudienceSegment(id="be13e6ca91/2103836", name="Segment One", member_count=3),
        AudienceSegment(id="be13e6ca91/2103837", name="Segment Two", member_count=1),
        AudienceSegment(id="be13e6ca91/2103838", name="Segment Three", member_count=1),
    ]


def test_get_audience_segments_list_not_found(backend: MockMailchimpCampaignBackend):
    backend.client.lists.list_segments.side_effect = ApiClientError("", 404)

    with pytest.raises(Audience.DoesNotExist):
        backend.get_audience_segments("be13e6ca91")


@pytest.mark.parametrize(
    "dotted_path,cls",
    [
        (None, MailchimpCampaignBackend),
        (f"{__name__}.CustomCampaignBackend", CustomCampaignBackend),
    ],
)
def test_get_backend_lookup(settings, dotted_path, cls):
    settings.WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY = "mock key"
    if dotted_path is None:
        del settings.WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND
    else:
        settings.WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND = dotted_path

    assert type(get_backend()) is cls
