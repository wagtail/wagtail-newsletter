from unittest.mock import Mock

import pytest

from django.test import Client
from django.urls import reverse
from wagtail.models import Page, Site

from tests.conftest import MemoryCampaignBackend
from wagtail_newsletter.actions import _log
from wagtail_newsletter.models import NewsletterLogEntry
from wagtail_newsletter.test.models import ArticlePage, SimplePage


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


def page_ptr(page: ArticlePage) -> Page:
    return page.page_ptr  # type: ignore


@pytest.mark.django_db
def test_log_entry_str(page: ArticlePage):
    entry = _log(page, "wagtail_newsletter.save_campaign")
    assert str(entry) == (
        f"NewsletterLogEntry {entry.pk}: 'wagtail_newsletter.save_campaign'"
        f" on 'Article Page' with id {page.pk}"
    )


def test_save_campaign(page: ArticlePage, admin_client: Client, admin_user):
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "save_campaign",
    }
    admin_client.post(url, data)

    assert [
        (entry.page, entry.user, entry.action)
        for entry in NewsletterLogEntry.objects.all()
    ] == [(page_ptr(page), admin_user, "wagtail_newsletter.save_campaign")]


def test_send_test_email(page: ArticlePage, admin_client: Client, admin_user):
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "send_test_email",
        "newsletter-test-email": EMAIL,
    }
    admin_client.post(url, data)

    assert [
        (entry.page, entry.user, entry.action)
        for entry in NewsletterLogEntry.objects.all()
    ] == [
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

    assert [
        (entry.page, entry.user, entry.action)
        for entry in NewsletterLogEntry.objects.all()
    ] == [
        (page_ptr(page), admin_user, "wagtail_newsletter.send_campaign"),
        (page_ptr(page), admin_user, "wagtail_newsletter.save_campaign"),
    ]


def test_history_view(page: ArticlePage, admin_client: Client):
    entry = _log(page, "wagtail_newsletter.save_campaign")
    url = reverse("wagtail_newsletter:history", kwargs={"page_id": page.pk})
    response = admin_client.get(url)
    assert response.status_code == 200
    assert list(response.context["object_list"]) == [entry]


def test_history_view_wrong_page_type(admin_client: Client):
    page = SimplePage(title="Simple Page")
    Site.objects.get().root_page.add_child(instance=page)
    url = reverse("wagtail_newsletter:history", kwargs={"page_id": page.pk})
    response = admin_client.get(url)
    assert response.status_code == 404


def test_history_view_permission_denied(
    page: ArticlePage, admin_client: Client, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        ArticlePage, "has_newsletter_permission", Mock(return_value=False)
    )
    url = reverse("wagtail_newsletter:history", kwargs={"page_id": page.pk})
    response = admin_client.get(url, follow=True)
    assert response.redirect_chain == [("/admin/", 302)]
    assert [m.message.strip() for m in response.context["messages"]] == [
        "Sorry, you do not have permission to access this area.",
    ]
