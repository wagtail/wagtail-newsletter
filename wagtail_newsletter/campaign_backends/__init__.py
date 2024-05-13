from abc import abstractmethod
from dataclasses import dataclass

from django.conf import settings
from django.utils.module_loading import import_string


DEFAULT_CAMPAIGN_BACKEND = (
    "wagtail_newsletter.campaign_backends.mailchimp.MailchimpCampaignBackend"
)


@dataclass
class Audience:
    id: str
    name: str
    member_count: int


@dataclass
class AudienceSegment:
    id: str
    name: str
    member_count: int


class AudienceNotFoundError(LookupError):
    pass


class CampaignBackend:
    @abstractmethod
    def get_audiences(self) -> "list[Audience]":
        raise NotImplementedError

    @abstractmethod
    def get_audience_segments(self, audience_id) -> "list[AudienceSegment]":
        raise NotImplementedError


def get_backend() -> CampaignBackend:
    backend_class = import_string(
        getattr(
            settings, "WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND", DEFAULT_CAMPAIGN_BACKEND
        )
    )
    return backend_class()
