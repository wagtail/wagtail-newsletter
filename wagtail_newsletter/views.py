from typing import cast

from django.apps import apps
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.html import format_html
from django.views.decorators.http import require_http_methods
from wagtail.admin import messages
from wagtail.log_actions import log, registry
from wagtail.models import Page

from . import campaign_backends, get_recipients_model_string
from .models import NewsletterPageMixin, NewsletterRecipientsBase


def has_permission_or_show_message(request, page, action):
    if page.has_newsletter_permission(request.user, action):
        return True

    else:
        label = registry.get_action_label(f"wagtail_newsletter.{action}")
        message = format_html(
            "You do not have permission to perform the action {}.", label
        )
        messages.error(request, message)
        return False


def recipients(request):
    model = apps.get_model(get_recipients_model_string())
    recipients: NewsletterRecipientsBase = get_object_or_404(
        model,  # type: ignore
        pk=request.GET.get("pk"),
    )

    return JsonResponse(
        {
            "name": recipients.name,
            "member_count": recipients.member_count,
        }
    )


@require_http_methods(["POST"])
def unschedule(request, page_id):
    page = cast(NewsletterPageMixin, get_object_or_404(Page, id=page_id).specific)

    if has_permission_or_show_message(request, page, "unschedule_campaign"):
        backend = campaign_backends.get_backend()

        try:
            backend.unschedule_campaign(page.newsletter_campaign)

        except campaign_backends.CampaignBackendError as error:
            messages.error(request, error.message)

        else:
            log(page, "wagtail_newsletter.unschedule_campaign")
            messages.success(request, "Campaign successfully unscheduled")

    return redirect("wagtailadmin_pages:edit", page_id=page_id)
