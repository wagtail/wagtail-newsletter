from unittest.mock import Mock, call

import pytest

from django.test import Client
from django.urls import reverse

from tests.conftest import MemoryCampaignBackend
from wagtail_newsletter.campaign_backends import CampaignBackendError
from wagtail_newsletter.test.models import ArticlePage


pytestmark = pytest.mark.django_db

CAMPAIGN_ID = "test-campaign-id"
CAMPAIGN_URL = "http://campaign.example.com"
EMAIL = "test@example.com"


def test_unschedule_campaign(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    memory_backend.unschedule_campaign = Mock()
    page.newsletter_campaign = CAMPAIGN_ID
    page.save()

    response = admin_client.post(
        reverse("wagtail_newsletter:unschedule", kwargs={"page_id": page.pk}),
        follow=True,
    )

    html = response.content.decode()
    assert "Campaign successfully unscheduled" in html

    assert memory_backend.unschedule_campaign.mock_calls == [call(CAMPAIGN_ID)]


def test_unschedule_campaign_failed(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.unschedule_campaign = Mock(
        side_effect=CampaignBackendError("Mock error")
    )

    response = admin_client.post(
        reverse("wagtail_newsletter:unschedule", kwargs={"page_id": page.pk}),
        follow=True,
    )

    assert "Mock error" in response.content.decode()
