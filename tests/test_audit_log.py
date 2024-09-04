from datetime import date, datetime, time, timedelta
from unittest.mock import Mock

import pytest

from django.test import Client
from django.urls import reverse
from wagtail.models import Page, PageLogEntry, Site

from tests.conftest import MemoryCampaignBackend
from wagtail_newsletter.test.models import ArticlePage


pytestmark = pytest.mark.django_db

CAMPAIGN_ID = "test-campaign-id"
CAMPAIGN_URL = "http://campaign.example.com"
EMAIL = "test@example.com"


@pytest.fixture
def page():
    page = ArticlePage(title="Test Article")
    Site.objects.get().root_page.add_child(instance=page)
    return page


@pytest.fixture(autouse=True)
def backend(memory_backend: MemoryCampaignBackend):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock()
    memory_backend.send_test_email = Mock()
    memory_backend.send_campaign = Mock()
    memory_backend.schedule_campaign = Mock()
    memory_backend.unschedule_campaign = Mock()


def page_ptr(page: ArticlePage) -> Page:
    return page.page_ptr  # type: ignore


def get_log_entries():
    return [
        (entry.page, entry.user, entry.action)
        for entry in PageLogEntry.objects.all()
        if entry.action.startswith("wagtail_newsletter.")
    ]


def test_save_campaign(page: ArticlePage, admin_client: Client, admin_user):
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "save_campaign",
    }
    admin_client.post(url, data)

    assert get_log_entries() == [
        (page_ptr(page), admin_user, "wagtail_newsletter.save_campaign"),
    ]


def test_send_test_email(page: ArticlePage, admin_client: Client, admin_user):
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "send_test_email",
        "newsletter-test-email": EMAIL,
    }
    admin_client.post(url, data)

    assert get_log_entries() == [
        (page_ptr(page), admin_user, "wagtail_newsletter.send_test_email"),
        (page_ptr(page), admin_user, "wagtail_newsletter.save_campaign"),
    ]


def test_send_campaign(page: ArticlePage, admin_client: Client, admin_user):
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "send_campaign",
    }
    admin_client.post(url, data)

    assert get_log_entries() == [
        (page_ptr(page), admin_user, "wagtail_newsletter.send_campaign"),
        (page_ptr(page), admin_user, "wagtail_newsletter.save_campaign"),
    ]


def test_schedule_campaign(page: ArticlePage, admin_client: Client, admin_user):
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    schedule_time = datetime.combine(date.today() + timedelta(days=1), time(12))
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "schedule_campaign",
        "newsletter-schedule-schedule_time": schedule_time.isoformat(),
    }
    admin_client.post(url, data)

    assert get_log_entries() == [
        (page_ptr(page), admin_user, "wagtail_newsletter.schedule_campaign"),
        (page_ptr(page), admin_user, "wagtail_newsletter.save_campaign"),
    ]


def test_unschedule_campaign(page: ArticlePage, admin_client: Client, admin_user):
    admin_client.post(
        reverse("wagtail_newsletter:unschedule", kwargs={"page_id": page.pk})
    )

    assert get_log_entries() == [
        (page_ptr(page), admin_user, "wagtail_newsletter.unschedule_campaign"),
    ]
