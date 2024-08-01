import logging

from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property
from django.utils.html import format_html
from wagtail.admin.panels import Panel

from . import campaign_backends, forms, models


logger = logging.getLogger(__name__)


class NewsletterPanel(Panel):
    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtail_newsletter/panels/newsletter_panel.html"

        instance: "models.NewsletterPageMixin"

        class Media:
            css = {"all": ["wagtail_newsletter/css/wagtail_newsletter.css"]}
            js = ["wagtail_newsletter/js/wagtail_newsletter.js"]

        @cached_property
        def permissions(self):
            return frozenset(
                action
                for action in [
                    "save_campaign",
                    "send_test_email",
                    "send_campaign",
                    "get_report",
                ]
                if self.instance.has_newsletter_permission(self.request.user, action)
            )

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context) or {}
            backend = campaign_backends.get_backend()
            campaign = None

            if self.instance.pk:
                if self.instance.newsletter_campaign:
                    try:
                        campaign = backend.get_campaign(
                            self.instance.newsletter_campaign
                        )

                        if campaign is None:
                            context["campaign_was_deleted"] = True
                            context["error_message"] = format_html(
                                """
                                The campaign <code>{deleted_campaign_id}</code> was
                                deleted in {backend_name}. Click <strong>Save
                                campaign to {backend_name}</strong> to recreate it.
                                """,
                                deleted_campaign_id=self.instance.newsletter_campaign,
                                backend_name=backend.name,
                            )

                    except ImproperlyConfigured:
                        logger.exception("Error loading campaign data")
                        context["error_message"] = (
                            "The newsletter campaign backend is not properly configured."
                        )

                    except campaign_backends.CampaignBackendError as error:
                        context["error_message"] = str(error)

            context["backend_name"] = backend.name
            context["campaign"] = campaign
            context["test_form"] = forms.SendTestEmailForm(
                initial={"email": self.request.user.email},
                prefix="newsletter-test",
            )

            if campaign is not None and campaign.sent:
                context["sent"] = True
                if "get_report" in self.permissions:
                    context["report"] = campaign.get_report()

            context["has_action_permission"] = {
                permission: True for permission in self.permissions
            }

            return context

        def is_shown(self):  # type: ignore
            return bool(self.permissions)
