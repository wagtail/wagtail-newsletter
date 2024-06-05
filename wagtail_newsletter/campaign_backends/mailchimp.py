from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from mailchimp_marketing import Client
from mailchimp_marketing.api_client import ApiClientError

from ..audiences import (
    Audience,
    AudienceSegment,
)
from . import CampaignBackend


class MailchimpCampaignBackend(CampaignBackend):
    name = "Mailchimp"

    def __init__(self):
        self.client = Client()
        self.client.set_config(self.get_client_config())

    def get_client_config(self) -> "dict[str, Any]":
        if not settings.WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY:
            raise ImproperlyConfigured(
                "WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY is not set"
            )

        return {
            "api_key": settings.WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY,
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

            raise

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
