from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from mailchimp_marketing import Client
from mailchimp_marketing.api_client import ApiClientError


@dataclass
class MailchimpAudience:
    id: str
    name: str
    member_count: int


@dataclass
class MailchimpAudienceSegment:
    id: str
    name: str
    member_count: int


class AudienceNotFoundError(LookupError):
    pass


class MailchimpCampaignBackend:
    def __init__(self):
        self.client = Client()
        self.client.set_config(self.get_client_config())

    def get_client_config(self):
        if not settings.WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY:
            raise ImproperlyConfigured(
                "WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY is not set"
            )

        return {
            "api_key": settings.WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY,
            "timeout": 30,
        }

    def get_audiences(self) -> "list[MailchimpAudience]":
        audiences = self.client.lists.get_all_lists()["lists"]
        return [
            MailchimpAudience(
                id=audience["id"],
                name=audience["name"],
                member_count=audience["stats"]["member_count"],
            )
            for audience in audiences
        ]

    def get_audience_segments(self, audience_id) -> "list[MailchimpAudienceSegment]":
        try:
            segments = self.client.lists.list_segments(audience_id)["segments"]

        except ApiClientError as error:
            if error.status_code == 404:
                raise AudienceNotFoundError from error

            raise

        return [
            MailchimpAudienceSegment(
                # Include the audience ID in the segment ID, so we can find the segment
                # later.
                id=f"{audience_id}/{segment['id']}",
                name=segment["name"],
                member_count=segment["member_count"],
            )
            for segment in segments
        ]
