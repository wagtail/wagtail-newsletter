import pytest

from django.test import Client
from django.urls import resolve, reverse
from wagtail.models import Site

from tests.conftest import MemoryCampaignBackend
from wagtail_newsletter.test.models import ArticlePage, CustomRecipients


pytestmark = pytest.mark.django_db


@pytest.fixture
def page():
    page = ArticlePage(title="Test Article")
    Site.objects.get().root_page.add_child(instance=page)
    return page


@pytest.mark.parametrize(
    "post_data,view_name",
    [
        ({}, "wagtailadmin_pages:edit"),
        ({"newsletter_action": "preview_campaign"}, "wagtail_newsletter:campaign"),
    ],
)
def test_save_revision_redirect(
    page: ArticlePage, admin_client: Client, post_data, view_name
):
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    data = {"title": page.title, "slug": page.slug, **post_data}
    response = admin_client.post(url, data)
    assert response.status_code == 302
    response_url = response.url  # type: ignore
    assert resolve(response_url).view_name == view_name


def test_campaign_view_context(page: ArticlePage, admin_client: Client):
    page.body = "Hello Test Campaign"
    page.newsletter_recipients = CustomRecipients.objects.create()
    url = reverse(
        "wagtail_newsletter:campaign",
        kwargs={"page_id": page.pk, "revision_id": page.save_revision().pk},
    )
    response = admin_client.get(url)
    context = dict(response.context)
    assert context["page"] == page
    assert context["campaign_data"]["recipients"] == page.newsletter_recipients
    assert context["campaign_data"]["subject"] == page.title
    assert (
        f'<h1 class="newsletter">{page.title}</h1>' in context["campaign_data"]["html"]
    )
    assert context["backend_name"] == MemoryCampaignBackend.name
