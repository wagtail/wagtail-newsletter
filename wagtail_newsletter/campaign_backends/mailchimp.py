from dataclasses import dataclass

from django.conf import settings
from mailchimp_marketing import Client


@dataclass
class MailchimpList:
    id: str
    name: str
    member_count: int


@dataclass
class MailchimpListSegment:
    id: str
    name: str
    member_count: int


class MailchimpCampaignBackend:
    def __init__(self):
        self.client = Client()
        self.client.set_config(self.get_client_config())

    def get_client_config(self):
        return {
            "api_key": settings.WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY,
            "timeout": 30,
        }

    def get_audiences(self) -> "list[MailchimpList]":
        audiences = self.client.lists.get_all_lists()["lists"]
        return [
            MailchimpList(
                id=audience["id"],
                name=audience["name"],
                member_count=audience["stats"]["member_count"],
            )
            for audience in audiences
        ]

    def get_audience_segments(self, audience_id) -> "list[MailchimpListSegment]":
        segments = self.client.lists.list_segments(audience_id)["segments"]
        return [
            MailchimpListSegment(
                id=f"{audience_id}/{segment['id']}",
                name=segment["name"],
                member_count=segment["member_count"],
            )
            for segment in segments
        ]
