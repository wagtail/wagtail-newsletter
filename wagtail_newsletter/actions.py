from typing import cast

from django.utils.formats import localize
from wagtail.admin import messages
from wagtail.log_actions import log

from . import campaign_backends, forms
from .models import NewsletterPageMixin


def save_campaign(request, page: NewsletterPageMixin) -> None:
    backend = campaign_backends.get_backend()
    revision = page.latest_revision
    version = cast(NewsletterPageMixin, revision.as_object())
    subject = version.get_newsletter_subject()

    try:
        campaign_id = backend.save_campaign(
            campaign_id=page.newsletter_campaign,
            recipients=version.newsletter_recipients,
            subject=subject,
            html=version.get_newsletter_html(),
        )

    except campaign_backends.CampaignBackendError as error:
        messages.error(request, error.message)
        return

    page.newsletter_campaign = campaign_id
    page.save(update_fields=["newsletter_campaign"])

    log(
        page,
        "wagtail_newsletter.save_campaign",
        revision=revision,
        timestamp=revision.created_at,
        content_changed=True,
    )

    messages.success(
        request, f"Newsletter campaign {subject!r} has been saved to {backend.name}"
    )


def send_test_email(request, page: NewsletterPageMixin) -> None:
    form = forms.SendTestEmailForm(request.POST, prefix="newsletter-test")
    if not form.is_valid():
        for field, errors in form.errors.items():
            for message in errors:
                messages.error(request, f"{form[field].label}: {message}")
        return

    email = form.cleaned_data["email"]

    save_campaign(request, page)

    backend = campaign_backends.get_backend()

    try:
        backend.send_test_email(
            campaign_id=page.newsletter_campaign,
            email=email,
        )

    except campaign_backends.CampaignBackendError as error:
        messages.error(request, error.message)
        return

    log(page, "wagtail_newsletter.send_test_email", data={"email": email})

    messages.success(request, f"Test message sent to {email!r}")


def send_campaign(request, page: NewsletterPageMixin) -> None:
    save_campaign(request, page)

    backend = campaign_backends.get_backend()

    try:
        backend.send_campaign(page.newsletter_campaign)

    except campaign_backends.CampaignBackendError as error:
        messages.error(request, error.message)
        return

    log(page, "wagtail_newsletter.send_campaign")

    messages.success(request, "Newsletter campaign is now sending")


def schedule_campaign(request, page: NewsletterPageMixin) -> None:
    form = forms.ScheduleCampaignForm(request.POST, prefix="newsletter-schedule")
    if not form.is_valid():
        for field, errors in form.errors.items():
            for message in errors:
                messages.error(request, f"{form[field].label}: {message}")
        return

    schedule_time = form.cleaned_data["schedule_time"]

    backend = campaign_backends.get_backend()

    try:
        backend.validate_schedule_time(schedule_time)
    except campaign_backends.CampaignBackendError as error:
        messages.error(request, error.message)
        return

    save_campaign(request, page)

    try:
        backend.schedule_campaign(
            campaign_id=page.newsletter_campaign,
            schedule_time=schedule_time,
        )

    except campaign_backends.CampaignBackendError as error:
        messages.error(request, error.message)
        return

    log(
        page,
        "wagtail_newsletter.schedule_campaign",
        data={"schedule_time": schedule_time},
    )

    when = f"{localize(schedule_time)} {schedule_time.tzname()}"
    messages.success(request, f"Campaign scheduled to send at {when}")
