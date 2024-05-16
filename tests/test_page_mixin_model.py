import pytest

from django.urls import reverse
from wagtail.models import Site

from wagtail_newsletter.test.models import ArticlePage, CustomRecipients


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
    assert page.newsletter_subject == "subject 2"
    assert page.newsletter_recipients == recipients_2
    assert page.newsletter_campaign == "campaign 2"
    assert page.body == "body 2"

    revs = [rev.as_object() for rev in page.revisions.all()]
    # All revisions should show the most recent values for the persistent fields.
    assert {rev.body for rev in revs} == {"body 2"}
    assert {rev.newsletter_recipients for rev in revs} == {recipients_2}
    assert {rev.newsletter_subject for rev in revs} == {"subject 2"}
    assert {rev.newsletter_campaign for rev in revs} == {"campaign 2"}
    # `title` is the control group. Its value should vary across versions.
    assert {rev.title for rev in revs} == {"title 1", "title 2"}


@pytest.mark.django_db
def test_admin_panels(admin_client):
    page = ArticlePage(title="title 0")
    Site.objects.get().root_page.add_child(instance=page)
    url = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.pk})
    response = admin_client.get(url)
    panels = {
        tab.heading: [panel.heading for panel in tab.children]
        for tab in dict(response.context)["edit_handler"].children
    }
    assert panels["Newsletter"] == ["Newsletter recipients", "Newsletter subject"]