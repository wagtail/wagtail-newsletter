from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import ANY, Mock, call

import pytest

from django.test import Client
from django.urls import reverse
from django.utils.formats import localize

from tests.conftest import MemoryCampaignBackend
from wagtail_newsletter.campaign_backends import CampaignBackendError
from wagtail_newsletter.test.models import ArticlePage


pytestmark = pytest.mark.django_db

CAMPAIGN_ID = "test-campaign-id"
CAMPAIGN_URL = "http://campaign.example.com"
EMAIL = "test@example.com"


def get_schedule_time(delta: timedelta):
    return datetime.combine(date.today() + delta, time(12))


def test_schedule_campaign(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    memory_backend.schedule_campaign = Mock()

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    schedule_time = get_schedule_time(timedelta(days=1))
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
    assert f"Campaign scheduled to send at {localize(schedule_time)}" in html

    assert memory_backend.save_campaign.mock_calls == [
        call(campaign_id="", recipients=None, subject=page.title, html=ANY)
    ]
    assert memory_backend.schedule_campaign.mock_calls == [
        call(
            campaign_id=CAMPAIGN_ID,
            schedule_time=schedule_time.replace(tzinfo=timezone.utc),
        )
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
    schedule_time = get_schedule_time(timedelta(days=1))
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "schedule_campaign",
        "newsletter-schedule-schedule_time": schedule_time.isoformat(),
    }
    response = admin_client.post(url, data, follow=True)

    assert "Mock error" in response.content.decode()


def test_schedule_in_the_past(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    schedule_time = get_schedule_time(timedelta(days=-1))
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "schedule_campaign",
        "newsletter-schedule-schedule_time": schedule_time.isoformat(),
    }
    response = admin_client.post(url, data, follow=True)

    assert "Schedule time: Date must be in the future." in response.content.decode()
