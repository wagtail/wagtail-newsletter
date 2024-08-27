from unittest.mock import ANY, Mock, call

import pytest

from django.test import Client
from django.urls import reverse
from wagtail.models import Site

from tests.conftest import MemoryCampaignBackend
from wagtail_newsletter.campaign_backends import CampaignBackendError
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


def test_save_campaign(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "save_campaign",
    }
    response = admin_client.post(url, data, follow=True)

    html = response.content.decode()
    assert f"Page &#x27;{page.title}&#x27; has been updated" in html
    assert (
        f"Newsletter campaign &#x27;{page.title}&#x27; has been saved to Testing"
        in html
    )
    assert f'href="{CAMPAIGN_URL}"' in html

    assert memory_backend.save_campaign.mock_calls == [
        call(campaign_id="", recipients=None, subject=page.title, html=ANY)
    ]

    page.refresh_from_db()
    assert page.newsletter_campaign == CAMPAIGN_ID


def test_save_campaign_failed_to_save(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(side_effect=CampaignBackendError("Mock error"))

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "save_campaign",
    }
    response = admin_client.post(url, data, follow=True)

    assert "Mock error" in response.content.decode()

    page.refresh_from_db()
    assert page.newsletter_campaign == ""


def test_send_test_email(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    memory_backend.send_test_email = Mock()

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "send_test_email",
        "newsletter-test-email": EMAIL,
    }
    response = admin_client.post(url, data, follow=True)

    html = response.content.decode()
    assert f"Page &#x27;{page.title}&#x27; has been updated" in html
    assert (
        f"Newsletter campaign &#x27;{page.title}&#x27; has been saved to Testing"
        in html
    )
    assert f"Test message sent to &#x27;{EMAIL}&#x27;" in html

    assert memory_backend.save_campaign.mock_calls == [
        call(campaign_id="", recipients=None, subject=page.title, html=ANY)
    ]
    assert memory_backend.send_test_email.mock_calls == [
        call(campaign_id=CAMPAIGN_ID, email=EMAIL)
    ]


def test_send_test_email_invalid_email(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.send_test_email = Mock()

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "send_test_email",
        "newsletter-test-email": "invalid-address",
    }
    response = admin_client.post(url, data, follow=True)

    html = response.content.decode()
    assert f"Page &#x27;{page.title}&#x27; has been updated" in html
    assert "&#x27;email&#x27;: Enter a valid email address." in html

    assert memory_backend.save_campaign.mock_calls == []
    assert memory_backend.send_test_email.mock_calls == []


def test_send_test_email_failed_to_send(
    page: ArticlePage, admin_client: Client, memory_backend: MemoryCampaignBackend
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    memory_backend.send_test_email = Mock(
        side_effect=CampaignBackendError("Mock error")
    )

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": "send_test_email",
        "newsletter-test-email": EMAIL,
    }
    response = admin_client.post(url, data, follow=True)

    assert "Mock error" in response.content.decode()


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


@pytest.mark.parametrize(
    "action", ["save_campaign", "send_test_email", "send_campaign"]
)
def test_action_restricted(
    page: ArticlePage,
    admin_client: Client,
    memory_backend: MemoryCampaignBackend,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    memory_backend.send_test_email = Mock()
    memory_backend.send_campaign = Mock()

    monkeypatch.setattr(
        ArticlePage, "has_newsletter_permission", Mock(return_value=False)
    )

    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {
        "title": page.title,
        "slug": page.slug,
        "newsletter-action": action,
    }
    response = admin_client.post(url, data, follow=True)

    html = response.content.decode()
    assert f"Page &#x27;{page.title}&#x27; has been updated" in html
    assert (
        "You do not have permission to perform "
        f"the newsletter action &#x27;{action}&#x27;" in html
    )

    assert memory_backend.save_campaign.mock_calls == []
    assert memory_backend.send_test_email.mock_calls == []
    assert memory_backend.send_campaign.mock_calls == []
