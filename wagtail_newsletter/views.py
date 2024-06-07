from typing import cast

from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import View
from wagtail.admin import messages
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
from wagtail.models import ContentType, Page, Revision

from . import campaign_backends
from .models import NewsletterPageMixin


class CampaignView(WagtailAdminTemplateMixin, View):
    template_name = "wagtail_newsletter/campaign.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        edit_url = reverse(
            "wagtailadmin_pages:edit", kwargs={"page_id": self.object.pk}
        )
        context.update(
            page=self.object,
            campaign_data=self.campaign_data,
            backend_name=self.backend.name,
            next_url=f"{edit_url}#tab-newsletter",
        )
        return context

    def dispatch(self, request: HttpRequest, *, page_id: int, revision_id: int):  # type: ignore
        self.object = cast(
            NewsletterPageMixin, get_object_or_404(Page, pk=page_id).specific
        )
        self.revision = cast(
            NewsletterPageMixin,
            get_object_or_404(
                Revision,
                base_content_type=ContentType.objects.get_for_model(Page),
                pk=revision_id,
            ).as_object(),
        )
        self.campaign_data = {
            "recipients": self.revision.newsletter_recipients,
            "subject": self.revision.newsletter_subject or self.revision.title,
            "html": self.revision.get_newsletter_html(),
        }

        self.backend = campaign_backends.get_backend()

        return super().dispatch(request)

    def get(self, request):
        return self.render_to_response(self.get_context_data())

    def post(self, request):
        try:
            campaign_id = self.backend.save_campaign(
                campaign_id=self.object.newsletter_campaign,
                **self.campaign_data,
            )

        except campaign_backends.CampaignBackendError:
            messages.error(request, "Failed to save campaign")
            return redirect(".")

        self.object.newsletter_campaign = campaign_id
        self.object.save(update_fields=["newsletter_campaign"])

        try:
            campaign = self.backend.get_campaign(campaign_id)
            if campaign is None:  # pragma: no cover
                raise RuntimeError("The campaign we just created is not there any more")

        except campaign_backends.CampaignBackendError:
            messages.error(request, "Failed to load campaign")
            return redirect(".")

        messages.success(
            request,
            f'Campaign "{self.campaign_data["subject"]}" saved successfully.',
            buttons=[
                messages.button(
                    campaign.url,
                    f"View in {self.backend.name}",
                    new_window=True,
                ),
            ],
        )

        return redirect(".")
