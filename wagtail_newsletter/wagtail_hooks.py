from django.urls import include, path
from django.views.i18n import JavaScriptCatalog
from wagtail import hooks

from . import DEFAULT_RECIPIENTS_MODEL, get_recipients_model_string, viewsets


@hooks.register("register_admin_urls")  # type: ignore
def register_admin_urls():
    urls = [
        path(
            "jsi18n/",
            JavaScriptCatalog.as_view(packages=["wagtail_newsletter"]),
            name="javascript_catalog",
        ),
        # Add your other URLs here, and they will appear under `/admin/newsletter/`
        # Note: you do not need to check for authentication in views added here, Wagtail does this for you!
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
    if get_recipients_model_string() == DEFAULT_RECIPIENTS_MODEL:
        register_viewsets.append(viewsets.newsletter_recipients_viewset)
    return register_viewsets
