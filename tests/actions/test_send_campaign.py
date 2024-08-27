from unittest.mock import ANY, Mock, call

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


def test_send_campaign(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    memory_backend.send_campaign = Mock()

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "send_campaign",
    }
    response = admin_client.post(url, data, follow=True)

    html = response.content.decode()
    assert f"Page &#x27;{page.title}&#x27; has been updated" in html
    assert (
        f"Newsletter campaign &#x27;{page.title}&#x27; has been saved to Testing"
        in html
    )
    assert "Newsletter campaign is now sending" in html

    assert memory_backend.save_campaign.mock_calls == [
        call(campaign_id="", recipients=None, subject=page.title, html=ANY)
    ]
    assert memory_backend.send_campaign.mock_calls == [call(CAMPAIGN_ID)]


def test_send_campaign_failed_to_send(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    memory_backend.send_campaign = Mock(side_effect=CampaignBackendError("Mock error"))

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "send_campaign",
    }
    response = admin_client.post(url, data, follow=True)

    assert "Mock error" in response.content.decode()
