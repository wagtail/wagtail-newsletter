import logging

from copy import deepcopy
from dataclasses import dataclass
from datetime import MINYEAR, datetime
from enum import Enum
from typing import NoReturn, Optional, cast

import requests

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.functional import cached_property

from ...audiences import Audience, AudienceSegment
from ...models import NewsletterRecipientsBase
from .. import Campaign, CampaignBackend, CampaignBackendError
from .._utils import _require_setting, valid_email
from .api import Client
from .api.campaigns import Campaign as CampaignT
from .api.errors import APIClientError


logger = logging.getLogger(__name__)


MINDATE = datetime(MINYEAR, 1, 1).isoformat()


class CampaignStatus(Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class ListmonkCampaign(Campaign):
    status: str
    backend: "ListmonkCampaignBackend"
    id: str

    @property
    def is_scheduled(self) -> bool:
        return self.status == CampaignStatus.SCHEDULED.value

    @property
    def is_sent(self) -> bool:
        return self.status == CampaignStatus.RUNNING.value

    @property
    def url(self) -> str:
        client: Client = self.backend.client
        return f"{client.campaigns.url}/{self.id}"

    def get_report(self):
        client: Client = self.backend.client
        try:
            data = client.campaigns.get_campaign(self.id)
        except APIClientError as error:
            _log_and_raise(
                error, "Error while fetching campaign statistics", campaign_id=self.id
            )
        report = {
            "emails_sent": data["data"]["sent"],
            "opens": data["data"]["views"],
            "bounces": data["data"]["bounces"],
            "clicks": data["data"]["clicks"],
        }
        send_at = data["data"]["send_at"]
        if send_at:
            try:
                report["send_time"] = datetime.fromisoformat(send_at)
            except ValueError:
                pass
        return report


@dataclass
class ListmonkCampaignBackend(CampaignBackend):
    name = "listmonk"
    campaign_class = ListmonkCampaign

    @cached_property
    def client(self) -> Client:
        base = _require_setting("WAGTAIL_NEWSLETTER_LISTMONK_BASE_URL")
        username = _require_setting("WAGTAIL_NEWSLETTER_LISTMONK_USER")
        token = _require_setting("WAGTAIL_NEWSLETTER_LISTMONK_API_KEY")
        auth = requests.auth.HTTPBasicAuth(username=username, password=token)
        client = Client(base, auth)
        return client

    def validate_recipients(
        self, recipients: Optional[NewsletterRecipientsBase]
    ) -> None:
        if recipients is None or not recipients.audience:
            raise ValidationError("listmonk requires an audience (list) to be selected")

    def get_audiences(self) -> list[Audience]:
        client: Client = self.client
        try:
            data = client.lists.get_apilists(per_page="all")["data"]
        except APIClientError as error:
            _log_and_raise(error, "Error while fetching audiences")

        return [Audience(id=item["id"], name=item["name"]) for item in data["results"]]

    def get_audience_segments(self, audience_id) -> list[AudienceSegment]:
        raise Audience.DoesNotExist from NotImplementedError(
            "AudiencesSegment not supported"
        )

    def get_campaign_request_params(
        self,
        *,
        body: str,
        recipients: Optional[NewsletterRecipientsBase],
        subject: str,
        name: str,
    ):
        email_name = _require_setting("WAGTAIL_NEWSLETTER_FROM_NAME")
        email = _require_setting("WAGTAIL_NEWSLETTER_REPLY_TO")
        from_email = f"{email_name} <{email}>"
        try:
            headers = _require_setting("WAGTAIL_NEWSLETTER_LISTMONK_HEADERS")
        except ImproperlyConfigured:
            headers = [{"Content-Type": "application/json", "charset": "utf-8"}]

        if not valid_email(from_email):
            raise ValidationError(f"from_email is not valid {from_email}")

        params = {
            "name": name,
            "subject": subject,
            "from_email": from_email,
            "content_type": "html",
            "messenger": "email",
            "type": "regular",
            "headers": headers,
            "body": body,
            "lists": [],
        }
        if recipients is not None:
            params["lists"].append(int(recipients.audience))
        return params

    def _create_campaign(self, **params) -> str:
        client: Client = self.client
        try:
            data = client.campaigns.create(**params)
        except APIClientError as error:
            _log_and_raise(error, "Error while creating campaign")

        new_campaign_id = data["data"]["id"]

        return str(new_campaign_id)

    def save_campaign(
        self,
        *,
        name: str,
        campaign_id: Optional[str] = None,
        recipients: Optional[NewsletterRecipientsBase],
        subject: str,
        html: str,
    ) -> str:
        client: Client = self.client

        params = self.get_campaign_request_params(
            name=name, body=html, recipients=recipients, subject=subject
        )
        if campaign_id:
            try:
                data = client.campaigns.update(id=int(campaign_id), **params)
                return str(data["data"]["id"])
            except APIClientError as error:
                if error.status_code == 400 and error.text == "invalid ID":
                    return self._create_campaign(**params)

                _log_and_raise(
                    error, "Error while updating campaign", campaign_id=campaign_id
                )
        return self._create_campaign(**params)

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        client: Client = self.client
        id = int(campaign_id)
        try:
            data = client.campaigns.get_campaign(id)
        except APIClientError as error:
            if error.status_code == 400 and error.text == "invalid ID":
                return None
            _log_and_raise(
                error, "Error while fetching campaign", campaign_id=campaign_id
            )
        status = data["data"]["status"]
        return self.campaign_class(
            backend=self,
            status=status,
            id=str(data["data"]["id"]),
        )

    def send_test_email(self, *, campaign_id: str, email: str) -> None:
        client: Client = self.client
        id = int(campaign_id)
        try:
            data = client.campaigns.get_campaign(id)["data"]
        except APIClientError as error:
            _log_and_raise(
                error, "Error while retrieving campaign data", campaign_id=campaign_id
            )
        lists = [item["id"] for item in data["lists"]]

        params = {
            "id": data["id"],
            "subscribers": [email],
            "name": data["name"],
            "subject": data["subject"],
            "lists": lists,
            "content_type": data["content_type"],
            "type": data["type"],
            "body": data["body"],
            "body_source": data["body_source"],
            "alt_body": data["altbody"],
            "from_email": data["from_email"],
            "messenger": data["messenger"],
            "tags": data["tags"],
            "send_at": data["send_at"],
            "template_id": data["template_id"],
            "headers": data["headers"],
        }

        try:
            test_email_data = client.campaigns.send_test_email(**params)  # type: ignore
        except APIClientError as error:
            _log_and_raise(
                error, "Error while sending test email", campaign_id=campaign_id
            )
        if test_email_data["data"] is False:
            _log_and_raise(
                APIClientError("Returned data is False"),
                "Error while sending test email",
                campaign_id=campaign_id,
            )

    def send_campaign(self, campaign_id: str) -> None:
        client: Client = self.client

        try:
            _ = client.campaigns.update_status(id=int(campaign_id), status="running")
        except APIClientError as error:
            _log_and_raise(
                error, "Error while sending campaign", campaign_id=campaign_id
            )

    def validate_schedule_time(self, schedule_time: datetime) -> None:
        """Validate schedule time. Override in subclass if backend has restrictions."""
        pass

    def schedule_campaign(self, campaign_id: str, schedule_time: datetime) -> None:
        client: Client = self.client
        id = int(campaign_id)
        try:
            data: CampaignT = client.campaigns.get_campaign(id)["data"]
        except APIClientError as error:
            _log_and_raise(
                error,
                "Error while getting campaign information",
                campaign_id=campaign_id,
            )
        params = deepcopy(data)
        for value in (
            "created_at",
            "archive",
            "archive_meta",
            "archive_slug",
            "archive_template_id",
            "bounces",
            "clicks",
            "media",
            "sent",
            "started_at",
            "status",
            "to_send",
            "updated_at",
            "uuid",
            "views",
        ):
            params.pop(value)
        altbody = params.pop("altbody")
        params = params | {"alt_body": altbody}
        lists = [item["id"] for item in params["lists"]]
        params["lists"]: list[int] = cast(list[int], lists)  # type: ignore
        params["send_at"] = schedule_time.isoformat()
        try:
            _ = client.campaigns.update(**params)  # type: ignore
        except APIClientError as error:
            _log_and_raise(
                error,
                "Error while setting campaign send_at time",
                campaign_id=campaign_id,
            )

        try:
            _ = client.campaigns.update_status(id=id, status="scheduled")
        except APIClientError as error:
            _log_and_raise(
                error, "Error while scheduling campaign", campaign_id=campaign_id
            )

    def unschedule_campaign(self, campaign_id: str) -> None:
        client: Client = self.client
        id = int(campaign_id)

        try:
            client.campaigns.update_status(
                id=id,
                status="draft",
            )  # NOTE: this relies on the backend response
            # to properly raise error if the origin
            # status is not compatible with draft
        except APIClientError as error:
            _log_and_raise(
                error, "Error while unscheduling campaign", campaign_id=campaign_id
            )


def _log_and_raise(error: APIClientError, message: str, **kwargs) -> NoReturn:
    kwargs["status_code"] = error.status_code
    kwargs["text"] = error.text
    logger.exception(
        f"{message}: {', '.join(f'{key}=%r' for key in kwargs.keys())}",
        *kwargs.values(),
    )
    raise CampaignBackendError(message) from error


__all__ = ["ListmonkCampaignBackend"]
