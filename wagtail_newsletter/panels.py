import logging

from django.core.exceptions import ImproperlyConfigured
from django.utils.html import format_html
from wagtail.admin.panels import Panel

from wagtail_newsletter.forms import SendTestEmailForm

from . import campaign_backends, models


logger = logging.getLogger(__name__)


class NewsletterPanel(Panel):
    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtail_newsletter/panels/newsletter_panel.html"

        instance: "models.NewsletterPageMixin"

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
            context["test_form"] = SendTestEmailForm(
                initial={"email": self.request.user.email},
            )

            if campaign is not None and campaign.sent:
                context["sent"] = True
                if self.instance.has_newsletter_permission(
                    self.request.user, "get_report"
                ):
                    context["report"] = campaign.get_report()

            context["has_action_permission"] = {}
            for action in ["save_campaign", "send_test_email", "send_campaign"]:
                if self.instance.has_newsletter_permission(self.request.user, action):
                    context["has_action_permission"][action] = True

            return context

        class Media:
            js = [
                "wagtail_newsletter/js/wagtail_newsletter.js",
            ]
