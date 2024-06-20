from unittest.mock import Mock

import pytest

from django.test import Client, RequestFactory
from django.urls import reverse
from wagtail.models import Page, Site

from wagtail_newsletter.test.models import ArticlePage, CustomRecipients, SimplePage


@pytest.mark.django_db
def test_persistent_fields(monkeypatch: pytest.MonkeyPatch):
    """
    The `newsletter_*` fields should always return the latest saved version of the data,
    as if they were not versioned at all.
    """

    # Users should be able to add their own newsletter-related persistent fields. We
    # simulate that by adding `body` to the list of persistent fields.
    monkeypatch.setattr(
        ArticlePage,
        "newsletter_persistent_fields",
        ArticlePage.newsletter_persistent_fields + ["body"],
    )

    recipients_1 = CustomRecipients(name="recipients 1")
    recipients_2 = CustomRecipients(name="recipients 2")
    CustomRecipients.objects.bulk_create([recipients_1, recipients_2])

    page = ArticlePage(title="title 0")
    Site.objects.get().root_page.add_child(instance=page)

    page.title = "title 1"
    page.newsletter_subject = "subject 1"
    page.newsletter_recipients = recipients_1
    page.newsletter_campaign = "campaign 1"
    page.body = "body 1"
    page.save_revision()

    page.title = "title 2"
    page.newsletter_subject = "subject 2"
    page.newsletter_recipients = recipients_2
    page.newsletter_campaign = "campaign 2"
    page.body = "body 2"
    page.save_revision()

    page.refresh_from_db()
    assert page.title == "title 0"
    assert page.newsletter_subject == ""
    assert page.newsletter_recipients is None
    assert page.newsletter_campaign == "campaign 2"
    assert page.body == "body 2"

    revs = [rev.as_object() for rev in page.revisions.all()]
    # All revisions should show the most recent values for the persistent field,
    # `newsletter_campaign`.
    assert {rev.body for rev in revs} == {"body 2"}
    assert {rev.newsletter_campaign for rev in revs} == {"campaign 2"}
    # `title`, `newsletter_recipients` and `newsletter_subject` should vary across
    # versions.
    assert {rev.title for rev in revs} == {"title 1", "title 2"}
    assert {rev.newsletter_recipients for rev in revs} == {recipients_1, recipients_2}
    assert {rev.newsletter_subject for rev in revs} == {"subject 1", "subject 2"}


@pytest.mark.django_db
def test_copy_clears_campaign(admin_client: Client):
    article = ArticlePage(title="Article", newsletter_campaign="test campaign")
    home: Page = Site.objects.get().root_page
    home.add_child(instance=article)
    response = admin_client.post(
        reverse("wagtailadmin_pages:copy", kwargs={"page_id": article.pk}),
        {
            "new_title": "Copy of Article",
            "new_slug": "copy-of-article",
            "new_parent_page": home.pk,
        },
    )
    assert response.status_code == 302
    new_article: ArticlePage = (  # type: ignore
        home.get_children().filter(slug="copy-of-article").get().specific  # type: ignore
    )
    assert new_article.newsletter_campaign == ""


@pytest.mark.django_db
def test_copy_regular_page_still_works(admin_client: Client):
    page = SimplePage(title="Page")
    home: Page = Site.objects.get().root_page
    home.add_child(instance=page)
    response = admin_client.post(
        reverse("wagtailadmin_pages:copy", kwargs={"page_id": page.pk}),
        {
            "new_title": "Copy of Page",
            "new_slug": "copy-of-page",
            "new_parent_page": home.pk,
        },
    )
    assert response.status_code == 302
    assert home.get_children().filter(slug="copy-of-page").exists()


def test_newsletter_html():
    page = ArticlePage(title="Page title")
    html = page.get_newsletter_html()
    assert '<h1 class="newsletter">Page title</h1>' in html


@pytest.mark.django_db
def test_newsletter_html_get_context():
    message = "THIS IS A TEST"

    class TestPage(ArticlePage):
        def get_newsletter_context(self):
            context = super().get_newsletter_context()
            context["message"] = message
            return context

        class Meta:  # type: ignore
            app_label = "wagtail_newsletter_test"

    page = TestPage()
    html = page.get_newsletter_html()
    assert f"<p>{message}</p>" in html


@pytest.mark.django_db
def test_newsletter_html_get_template():
    page = ArticlePage()
    page.get_newsletter_template = Mock(side_effect=page.get_newsletter_template)
    page.get_newsletter_html()
    assert page.get_newsletter_template.call_count == 1


def test_preview_default():
    page = ArticlePage(title="Page title")
    request = RequestFactory().get("/")
    response = page.serve_preview(request, "default").render()  # type: ignore
    assert b'<h1 class="web">Page title</h1>' in response.content


def test_preview_newsletter():
    page = ArticlePage(title="Page title")
    request = RequestFactory().get("/")
    response = page.serve_preview(request, "newsletter")
    assert '<h1 class="newsletter">Page title</h1>' in response.content.decode()
