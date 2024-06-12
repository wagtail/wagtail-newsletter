from typing import cast

from wagtail.admin import messages

from . import campaign_backends
from .models import NewsletterPageMixin


def save_campaign(request, page: NewsletterPageMixin) -> None:
    backend = campaign_backends.get_backend()
    revision = cast(NewsletterPageMixin, page.latest_revision.as_object())
    subject = revision.newsletter_subject or revision.title

    try:
        campaign_id = backend.save_campaign(
            campaign_id=page.newsletter_campaign,
            recipients=revision.newsletter_recipients,
            subject=subject,
            html=revision.get_newsletter_html(),
        )

    except campaign_backends.CampaignBackendError:
        messages.error(request, "Failed to save newsletter campaign")
        return

    page.newsletter_campaign = campaign_id
    page.save(update_fields=["newsletter_campaign"])

    messages.success(
        request, f"Newsletter campaign {subject!r} has been saved to {backend.name}"
    )
