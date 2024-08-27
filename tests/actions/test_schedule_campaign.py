from datetime import datetime, timezone
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
SCHEDULE_TIME = datetime(2024, 8, 10, 16, 30, tzinfo=timezone.utc)


def test_schedule_campaign(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    memory_backend.schedule_campaign = Mock()

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    schedule_time = SCHEDULE_TIME.replace(tzinfo=None)
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "schedule_campaign",
        "newsletter-schedule-schedule_time": schedule_time.isoformat(),
    }
    response = admin_client.post(url, data, follow=True)

    html = response.content.decode()
    assert f"Page &#x27;{page.title}&#x27; has been updated" in html
    assert (
        f"Newsletter campaign &#x27;{page.title}&#x27; has been saved to Testing"
        in html
    )
    assert "Campaign scheduled to send at Aug. 10, 2024, 4:30 p.m. UTC" in html

    assert memory_backend.save_campaign.mock_calls == [
        call(campaign_id="", recipients=None, subject=page.title, html=ANY)
    ]
    assert memory_backend.schedule_campaign.mock_calls == [
        call(campaign_id=CAMPAIGN_ID, schedule_time=SCHEDULE_TIME)
    ]


def test_schedule_campaign_failed_to_schedule(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    memory_backend.schedule_campaign = Mock(
        side_effect=CampaignBackendError("Mock error")
    )

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    schedule_time = SCHEDULE_TIME.replace(tzinfo=None)
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "schedule_campaign",
        "newsletter-schedule-schedule_time": schedule_time.isoformat(),
    }
    response = admin_client.post(url, data, follow=True)

    assert "Mock error" in response.content.decode()
