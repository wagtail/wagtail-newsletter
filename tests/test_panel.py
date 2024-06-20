import re

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from django.core.exceptions import ImproperlyConfigured
from django.test import Client
from django.urls import reverse
from wagtail.models import Site

from tests.conftest import MemoryCampaignBackend
from wagtail_newsletter.campaign_backends import CampaignBackendError
from wagtail_newsletter.test.models import ArticlePage


CAMPAIGN_ID = "test-campaign-id"
CAMPAIGN_URL = "http://campaign.example.com"
BACKEND_ERROR_TEXT = "something failed"


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "page_exists",
    [True, False],
)
def test_panels(admin_client: Client, page_exists):
    home_page = Site.objects.get().root_page

    if page_exists:
        page = ArticlePage(title="title 0")
        home_page.add_child(instance=page)
        url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})

    else:
        url = reverse(
            "wagtailadmin_pages:add",
            kwargs={
                "content_type_app_name": "wagtail_newsletter_test",
                "content_type_model_name": "articlepage",
                "parent_page_id": home_page.pk,
            },
        )

    response = admin_client.get(url)
    panels = {
        tab.heading: [panel.heading for panel in tab.children]
        for tab in dict(response.context)["edit_handler"].children
    }
    assert panels["Newsletter"] == ["Recipients", "Subject", "Campaign"]


def test_link_to_backend(admin_client: Client, memory_backend: MemoryCampaignBackend):
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    page = ArticlePage(title="Page title", newsletter_campaign="test-campaign-id")
    Site.objects.get().root_page.add_child(instance=page)
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    response = admin_client.get(url)
    assert f'href="{CAMPAIGN_URL}"' in response.content.decode()


def test_warn_improperly_configured(
    admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.get_campaign = Mock(side_effect=ImproperlyConfigured)
    page = ArticlePage(title="Page title", newsletter_campaign="test-campaign-id")
    Site.objects.get().root_page.add_child(instance=page)
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    response = admin_client.get(url)
    assert (
        "The newsletter campaign backend is not properly configured."
        in response.content.decode()
    )


def test_warn_deleted_campaign(
    admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.get_campaign = Mock(return_value=None)
    page = ArticlePage(title="Page title", newsletter_campaign=CAMPAIGN_ID)
    Site.objects.get().root_page.add_child(instance=page)
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    response = admin_client.get(url)
    assert f"The campaign <code>{CAMPAIGN_ID}</code> was deleted" in re.sub(
        r"\s+", " ", response.content.decode()
    )


def test_warn_backend_error(
    admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.get_campaign = Mock(
        side_effect=CampaignBackendError(BACKEND_ERROR_TEXT)
    )
    page = ArticlePage(title="Page title", newsletter_campaign=CAMPAIGN_ID)
    Site.objects.get().root_page.add_child(instance=page)
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    response = admin_client.get(url)
    assert BACKEND_ERROR_TEXT in response.content.decode()


@pytest.mark.parametrize("has_permission", [True, False])
def test_campaign_report(
    admin_client: Client,
    memory_backend: MemoryCampaignBackend,
    monkeypatch: pytest.MonkeyPatch,
    has_permission: bool,
):
    monkeypatch.setattr(
        ArticlePage, "has_newsletter_permission", Mock(return_value=has_permission)
    )
    campaign = Mock(status="sent")
    memory_backend.get_campaign = Mock(return_value=campaign)
    report = {
        "bounces": 6,
        "clicks": 3,
        "emails_sent": 13,
        "opens": 5,
        "send_time": datetime(2024, 6, 17, 12, 51, 46, tzinfo=timezone.utc),
    }
    campaign.get_report.return_value = report
    page = ArticlePage(title="Page title", newsletter_campaign="test-campaign-id")
    Site.objects.get().root_page.add_child(instance=page)
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    response = admin_client.get(url)
    context = dict(response.context)
    html = response.content.decode()

    if has_permission:
        assert re.search(r"<b>Status:</b>\s*sent", html)
        assert "report" in context
        assert re.search(r"<b>Send time:</b>\s*June 17, 2024, 12:51 p\.m\.", html)
        assert re.search(r"<b>Emails sent:</b>\s*13 \(6 bounces\)", html)
        assert re.search(r"<b>Opens:</b>\s*5", html)
        assert re.search(r"<b>Clicks:</b>\s*3", html)

    else:
        assert "report" not in context
