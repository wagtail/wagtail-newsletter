from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from django.conf import settings
from django.utils.module_loading import import_string

from .. import audiences, models


DEFAULT_CAMPAIGN_BACKEND = (
    "wagtail_newsletter.campaign_backends.mailchimp.MailchimpCampaignBackend"
)


class Campaign(ABC):
    @property
    @abstractmethod
    def is_scheduled(self) -> bool: ...

    @property
    @abstractmethod
    def is_sent(self) -> bool: ...

    @property
    @abstractmethod
    def url(self) -> str: ...

    @abstractmethod
    def get_report(self) -> "dict[str, Any]": ...


class CampaignBackend(ABC):
    name: str

    @abstractmethod
    def get_audiences(self) -> "list[audiences.Audience]": ...

    @abstractmethod
    def get_audience_segments(
        self, audience_id
    ) -> "list[audiences.AudienceSegment]": ...

    @abstractmethod
    def save_campaign(
        self,
        *,
        campaign_id: Optional[str] = None,
        recipients: "Optional[models.NewsletterRecipientsBase]",
        subject: str,
        html: str,
    ) -> str: ...

    @abstractmethod
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]: ...

    @abstractmethod
    def send_test_email(self, *, campaign_id: str, email: str) -> None: ...

    @abstractmethod
    def send_campaign(self, campaign_id: str) -> None: ...

    def validate_schedule_time(self, schedule_time: datetime) -> None:  # noqa: B027
        """Validate schedule time. Override in subclass if backend has restrictions."""
        pass

    @abstractmethod
    def schedule_campaign(self, campaign_id: str, schedule_time: datetime) -> None: ...

    @abstractmethod
    def unschedule_campaign(self, campaign_id: str) -> None: ...


def get_backend() -> CampaignBackend:
    backend_class = import_string(
        getattr(
            settings, "WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND", DEFAULT_CAMPAIGN_BACKEND
        )
    )
    return backend_class()


class CampaignBackendError(Exception):
    """The campaign backend encountered an error"""

    def __init__(self, message):
        self.message = message
