from typing import cast

from django.utils.formats import localize
from wagtail.admin import messages
from wagtail.log_actions import log

from . import campaign_backends, forms
from .models import NewsletterPageMixin


def save_campaign(
    request, page: NewsletterPageMixin, raise_on_empty_recipients: bool = False
) -> None:
    """
    Raises:
        ValueError: If backend is listmonk and recipients or recipients' audience is
        None
    """
    backend = campaign_backends.get_backend()
    revision = page.latest_revision
    version = cast(NewsletterPageMixin, revision.as_object())
    subject = version.get_newsletter_subject()
    title = page.title

    recipients = version.newsletter_recipients

    if backend.name == "listmonk" and (recipients is None or not recipients.audience):
        msg = "listmonk requires an audience (list) to be selected when creating a campaign"
        if raise_on_empty_recipients:
            raise ValueError(msg)
        messages.error(request, msg)

    try:
        campaign_id = backend.save_campaign(
            name=title,
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

    try:
        save_campaign(request, page, raise_on_empty_recipients=True)
    except ValueError as error:
        messages.error(request, error)
        return

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
