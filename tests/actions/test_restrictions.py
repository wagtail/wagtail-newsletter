from unittest.mock import Mock

import pytest

from django.test import Client
from django.urls import reverse

from tests.conftest import MemoryCampaignBackend
from wagtail_newsletter.test.models import ArticlePage


pytestmark = pytest.mark.django_db

CAMPAIGN_ID = "test-campaign-id"
CAMPAIGN_URL = "http://campaign.example.com"


@pytest.mark.parametrize(
    "action,label",
    [
        ("save_campaign", "Newsletter: Save campaign"),
        ("send_test_email", "Newsletter: Send test email"),
        ("send_campaign", "Newsletter: Send campaign"),
        ("schedule_campaign", "Newsletter: Schedule campaign"),
        ("unschedule_campaign", "Newsletter: Unschedule campaign"),
    ],
)
def test_action_restricted(
    page: ArticlePage,
    admin_client: Client,
    memory_backend: MemoryCampaignBackend,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    label: str,
):
    memory_backend.save_campaign = Mock(return_value=CAMPAIGN_ID)
    memory_backend.get_campaign = Mock(return_value=Mock(url=CAMPAIGN_URL))
    memory_backend.send_test_email = Mock()
    memory_backend.send_campaign = Mock()
    memory_backend.schedule_campaign = Mock()
    memory_backend.unschedule_campaign = Mock()

    monkeypatch.setattr(
        ArticlePage, "has_newsletter_permission", Mock(return_value=False)
    )

    if action == "unschedule_campaign":
        response = admin_client.post(
            reverse("wagtail_newsletter:unschedule", kwargs={"page_id": page.pk}),
            follow=True,
        )

    else:
        url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
        data = {
            "title": page.title,
            "slug": page.slug,
            "newsletter-action": action,
        }
        response = admin_client.post(url, data, follow=True)

    html = response.content.decode()

    if action != "unschedule_campaign":
        assert f"Page &#x27;{page.title}&#x27; has been updated" in html

    assert f"You do not have permission to perform the action {label}" in html

    assert memory_backend.save_campaign.mock_calls == []
    assert memory_backend.send_test_email.mock_calls == []
    assert memory_backend.send_campaign.mock_calls == []
