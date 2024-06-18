from typing import cast

from django.contrib.auth.models import Permission
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog
from wagtail import hooks
from wagtail.admin import messages
from wagtail.models import Page

from . import (
    DEFAULT_RECIPIENTS_MODEL,
    actions,
    get_recipients_model_string,
    views,
    viewsets,
)
from .models import NewsletterPageMixin


@hooks.register("register_admin_urls")  # type: ignore
def register_admin_urls():
    urls = [
        path(
            "jsi18n/",
            JavaScriptCatalog.as_view(packages=["wagtail_newsletter"]),
            name="javascript_catalog",
        ),
        path("recipients/", views.recipients, name="recipients"),
    ]

    return [
        path(
            "newsletter/",
            include(
                (urls, "wagtail_newsletter"),
                namespace="wagtail_newsletter",
            ),
        )
    ]


@hooks.register("register_admin_viewset")  # type: ignore
def register_admin_viewset():
    register_viewsets = [
        viewsets.audience_chooser_viewset,
        viewsets.audience_segment_chooser_viewset,
        viewsets.recipients_chooser_viewset,
    ]
    if get_recipients_model_string() == DEFAULT_RECIPIENTS_MODEL:  # pragma: no cover
        register_viewsets.append(viewsets.newsletter_recipients_viewset)
    return register_viewsets


@hooks.register("register_permissions")  # type: ignore
def register_permissions():  # pragma: no cover
    if get_recipients_model_string() == DEFAULT_RECIPIENTS_MODEL:
        return Permission.objects.filter(
            content_type__app_label="wagtail_newsletter",
            codename__in=[
                "add_newsletterrecipients",
                "change_newsletterrecipients",
                "delete_newsletterrecipients",
            ],
        )

    else:
        return Permission.objects.none()


@hooks.register("after_create_page")  # type: ignore
@hooks.register("after_edit_page")  # type: ignore
def redirect_to_campaign_page(request, page: Page):
    action = request.POST.get("newsletter-action")

    if action is None:  # pragma: no cover
        return

    page = cast(NewsletterPageMixin, page)

    if not page.has_newsletter_permission(request.user, action):
        messages.error(
            request,
            f"You do not have permission to perform the newsletter action {action!r}.",
        )
        return

    if action == "save_campaign":
        actions.save_campaign(request, page)

    if action == "send_test_email":
        actions.send_test_email(request, page)

    if action == "send_campaign":
        actions.send_campaign(request, page)
