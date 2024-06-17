import logging

from copy import copy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, NoReturn, Optional, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property
from mailchimp_marketing import Client
from mailchimp_marketing.api_client import ApiClientError

from ..audiences import (
    Audience,
    AudienceSegment,
)
from ..models import NewsletterRecipientsBase
from . import Campaign, CampaignBackend, CampaignBackendError


CAMPAIGN_STATUS_DRAFT = "save"

logger = logging.getLogger(__name__)


@dataclass
class MailchimpCampaign(Campaign):
    backend: "MailchimpCampaignBackend"
    id: str
    web_id: str
    status: str

    @property
    def sent(self) -> bool:
        return self.status != CAMPAIGN_STATUS_DRAFT

    @property
    def url(self) -> str:
        server = self.backend.client.api_client.server
        base_url = f"https://{server}.admin.mailchimp.com"

        if self.sent:
            return f"{base_url}/reports/summary?id={self.web_id}"

        else:
            return f"{base_url}/campaigns/edit?id={self.web_id}"

    def get_report(self) -> "dict[str, Any]":
        try:
            data = self.backend.client.reports.get_campaign_report(self.id)

        except ApiClientError as error:
            _log_and_raise(
                error, "Error while fetching campaign report", campaign_id=self.id
            )

        report = {
            "emails_sent": data["emails_sent"],
            "bounces": sum(data["bounces"].values()),
            "opens": data["opens"]["unique_opens"],
            "clicks": data["clicks"]["unique_clicks"],
        }
        if data["send_time"]:
            report["send_time"] = datetime.fromisoformat(data["send_time"])
        return report


class MailchimpCampaignBackend(CampaignBackend):
    name = "Mailchimp"
    campaign_class = MailchimpCampaign

    @cached_property
    def client(self):
        client = Client()
        client.set_config(self.get_client_config())
        return client

    def get_client_config(self) -> "dict[str, Any]":
        return {
            "api_key": _require_setting("WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY"),
            "timeout": 30,
        }

    def get_audiences(self) -> "list[Audience]":
        audiences = self.client.lists.get_all_lists()["lists"]
        return [
            Audience(
                id=audience["id"],
                name=audience["name"],
                member_count=audience["stats"]["member_count"],
            )
            for audience in audiences
        ]

    def get_audience_segments(self, audience_id) -> "list[AudienceSegment]":
        try:
            segments = self.client.lists.list_segments(audience_id)["segments"]

        except ApiClientError as error:
            if error.status_code == 404:
                raise Audience.DoesNotExist from error

            _log_and_raise(
                error, "Error while fetching audience segments", audience_id=audience_id
            )

        return [
            AudienceSegment(
                # Include the audience ID in the segment ID, so we can find the segment
                # later.
                id=f"{audience_id}/{segment['id']}",
                name=segment["name"],
                member_count=segment["member_count"],
            )
            for segment in segments
        ]

    def _create_campaign(self, body) -> str:
        body = copy(body)
        body.setdefault("type", "regular")
        try:
            return cast(str, self.client.campaigns.create(body)["id"])

        except ApiClientError as error:
            _log_and_raise(error, "Error while creating campaign")

    def _update_campaign(self, campaign_id: str, body) -> str:
        try:
            self.client.campaigns.update(campaign_id, body)
            return campaign_id

        except ApiClientError as error:
            if error.status_code == 404:
                # The campaign was deleted on the Mailchimp end; create a new one
                return self._create_campaign(body)

            _log_and_raise(
                error, "Error while updating campaign", campaign_id=campaign_id
            )

    def _set_content(self, campaign_id: str, html: str) -> None:
        try:
            self.client.campaigns.set_content(campaign_id, {"html": html})

        except ApiClientError as error:
            _log_and_raise(
                error, "Error while saving campaign content", campaign_id=campaign_id
            )

    def get_campaign_request_body(
        self,
        *,
        recipients: Optional[NewsletterRecipientsBase],
        subject: str,
    ) -> "dict[str, Any]":
        body = {
            "settings": {
                "from_name": _require_setting("WAGTAIL_NEWSLETTER_FROM_NAME"),
                "reply_to": _require_setting("WAGTAIL_NEWSLETTER_REPLY_TO"),
                "subject_line": subject,
            },
        }

        if recipients is not None:
            body["recipients"] = {
                "list_id": recipients.audience,
            }

            if recipients.segment:
                segment_id = int(recipients.segment.split("/")[1])
                body["recipients"]["segment_opts"] = {
                    "saved_segment_id": segment_id,
                }

        return body

    def save_campaign(
        self,
        *,
        campaign_id: Optional[str] = None,
        recipients: Optional[NewsletterRecipientsBase],
        subject: str,
        html: str,
    ) -> str:
        body = self.get_campaign_request_body(recipients=recipients, subject=subject)

        if campaign_id:
            campaign_id = self._update_campaign(campaign_id, body)

        else:
            campaign_id = self._create_campaign(body)

        self._set_content(campaign_id, html)
        return campaign_id

    def get_campaign(self, campaign_id: str) -> Optional[MailchimpCampaign]:
        try:
            data = self.client.campaigns.get(campaign_id)

        except ApiClientError as error:
            if error.status_code == 404:
                return None

            _log_and_raise(
                error, "Error while fetching campaign", campaign_id=campaign_id
            )

        return self.campaign_class(
            backend=self,
            id=campaign_id,
            web_id=data["web_id"],
            status=data["status"],
        )

    def send_test_email(self, *, campaign_id: str, email: str) -> None:
        try:
            self.client.campaigns.send_test_email(
                campaign_id,
                {
                    "test_emails": [email],
                    "send_type": "html",
                },
            )

        except ApiClientError as error:
            _log_and_raise(
                error, "Error while sending test email", campaign_id=campaign_id
            )

    def send_campaign(self, campaign_id: str) -> None:
        try:
            self.client.campaigns.send(campaign_id)

        except ApiClientError as error:
            _log_and_raise(
                error, "Error while sending campaign", campaign_id=campaign_id
            )


def _log_and_raise(error: ApiClientError, message: str, **kwargs) -> NoReturn:
    kwargs["status_code"] = error.status_code
    kwargs["text"] = error.text
    logger.exception(
        f"{message}: {', '.join(f'{key}=%r' for key in kwargs.keys())}",
        *kwargs.values(),
    )
    raise CampaignBackendError(message) from error


def _require_setting(name):
    value = getattr(settings, name, None)
    if value is None:
        raise ImproperlyConfigured(f"{name} is not set")
    return value
