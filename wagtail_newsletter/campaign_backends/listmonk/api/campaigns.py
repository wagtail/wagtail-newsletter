import logging

from typing import Literal, Optional, TypedDict, cast
from urllib.parse import urljoin

import requests

from django.core.exceptions import ValidationError

from ..._utils import valid_time
from .errors import _handle_response


logger = logging.getLogger(__name__)


class SendContainer(TypedDict):
    data: bool


class DeleteContainer(TypedDict):
    data: bool


class Analytics(TypedDict):
    campaign_id: int
    count: int
    timestamp: str


class AnalyticsContainer(TypedDict):
    data: list[Analytics]


class SubscriptionList(TypedDict):
    id: int
    name: str


class Stats(TypedDict):
    id: int
    status: str
    to_send: int
    sent: int
    started_at: Optional[str]
    updated_at: Optional[str]
    rate: int
    net_rate: int


class StatsContainer(TypedDict):
    data: list[Stats]


class Campaign(TypedDict):
    id: int
    created_at: str
    updated_at: str
    views: int
    clicks: int
    bounces: int
    lists: list[SubscriptionList]
    started_at: Optional[str]
    to_send: int
    sent: int
    uuid: str
    type: Literal["regular", "optin"]
    name: str
    subject: str
    from_email: str
    body: str
    body_source: Optional[str]
    altbody: Optional[str]
    send_at: Optional[str]
    status: str
    content_type: Literal["richtext", "html", "markdown", "plain"]
    tags: list[str]
    template_id: int
    messenger: str
    media: list
    headers: list[dict[str, str]]
    archive: bool
    archive_meta: dict
    archive_slug: Optional[str]
    archive_template_id: Optional[int]


class Campaigns(TypedDict):
    results: list[Campaign]
    query: str
    total: int
    per_page: int
    page: int
    search: str


class CampaignsContainer(TypedDict):
    data: Campaigns


class CampaignContainer(TypedDict):
    data: Campaign


class APICampaigns:
    """
    Interact with API endpoint `listmonk /campaigns https://listmonk.app/docs/apis/campaigns/`_
    """

    endpoint = "/api/campaigns"

    def __init__(self, base: str, session: requests.Session):
        self.session = session
        self.base = base

    @property
    def url(self):
        return urljoin(self.base, self.endpoint)

    def get_campaigns(
        self,
        status: Optional[Literal["scheduled", "running", "paused", "cancelled"]] = None,
        no_body: Optional[bool] = None,
        page: Optional[int] = None,
        per_page: Optional[int | Literal["all"]] = None,
        tags: Optional[list[str]] = None,
        order: Optional[Literal["ASC", "DESC"]] = None,
        order_by: Optional[
            Literal["name", "status", "created_at", "updated_at"]
        ] = None,
        query: Optional[str] = None,
    ) -> CampaignsContainer:
        """
        See `GET /api/campaigns
        https://listmonk.app/docs/apis/campaigns/#get-apicampaigns`_
        """
        params = {
            "status": status,
            "no_body": no_body,
            "page": page,
            "per_page": per_page,
            "tags": tags,
            "order": order,
            "order_by": order_by,
            "query": query,
        }
        response = self.session.get(self.url, params=params)
        data: CampaignsContainer = cast(CampaignsContainer, _handle_response(response))

        return data

    def create(
        self,
        name: str,
        subject: str,
        lists: list[int],
        content_type: Literal["richtext", "html", "markdown", "plain", "visual"],
        type: Literal["optin", "regular"],
        body: str,
        body_source: Optional[str] = None,
        alt_body: Optional[str] = None,
        from_email: Optional[str] = None,
        messenger: Optional[str] = None,
        tags: Optional[list[str]] = None,
        send_at: Optional[str] = None,
        template_id: Optional[int] = None,
        headers: Optional[list[dict[str, str]]] = None,
    ) -> CampaignContainer:
        """
        Create compaign

        See `POST /api/campaigns https://listmonk.app/docs/apis/campaigns/#post-apicampaigns`_
        """
        url = self.url
        if send_at is not None:
            if not valid_time(send_at):
                raise ValidationError("send_at not in ISO8601 format")
        d = {
            "name": name,
            "subject": subject,
            "lists": lists,
            "content_type": content_type,
            "type": type,
            "body": body,
            "altbody": alt_body,
            "body_source": body_source,
            "from_email": from_email,
            "messenger": messenger,
            "tags": tags,
            "send_at": send_at,
            "template_id": template_id,
            "headers": headers,
        }
        response = self.session.post(
            url,
            json={k: v for k, v in d.items() if v is not None},
        )
        data: CampaignContainer = cast(CampaignContainer, _handle_response(response))

        return data

    def get_campaign(
        self, id: int, no_body: Optional[bool] = None
    ) -> CampaignContainer:
        """
        See `GET /api/campaigns/{campaign_id} https://listmonk.app/docs/apis/campaigns/#get-apicampaignscampaign_id`_
        """
        url = urljoin(self.base, f"{self.endpoint}/{id}")
        response = self.session.get(url, params={"no_body": no_body})
        data: CampaignContainer = cast(CampaignContainer, _handle_response(response))
        return data

    def get_running_stats(self, id: int) -> StatsContainer:
        """
        See `GET /api/campaigns/running/stats https://listmonk.app/docs/apis/campaigns/#get-apicampaignsrunningstats`_
        """
        url = urljoin(self.base, f"{self.endpoint}/running/stats")
        response = self.session.get(url, params={"campaign_id": id})
        data: StatsContainer = cast(StatsContainer, _handle_response(response))
        return data

    def get_analytics(
        self,
        id: int,
        type: Literal["links", "views", "clicks", "bounces"],
        from_: str,
        to: str,
    ) -> AnalyticsContainer:
        """
        See `GET /api/campaigns/analytics/{type} https://listmonk.app/docs/apis/campaigns/#get-apicampaignsanalyticstype`_
        """
        url = urljoin(self.base, f"{self.endpoint}/analytics/{type}")
        response = self.session.get(url, params={"to": to, "id": id, "from": from_})
        data: AnalyticsContainer = cast(AnalyticsContainer, _handle_response(response))
        return data

    def update(
        self,
        id: int,
        name: str,
        subject: str,
        lists: list[int],
        content_type: Literal["richtext", "html", "markdown", "plain", "visual"],
        type: Literal["optin", "regular"],
        body: str,
        body_source: Optional[str] = None,
        alt_body: Optional[str] = None,
        from_email: Optional[str] = None,
        messenger: Optional[str] = None,
        tags: Optional[list[str]] = None,
        send_at: Optional[str] = None,
        template_id: Optional[int] = None,
        headers: Optional[list[dict[str, str]]] = None,
    ) -> CampaignContainer:
        """
        See `PUT /api/campaigns/{campaign_id} https://listmonk.app/docs/apis/campaigns/#put-apicampaignscampaign_id`_
        """
        url = urljoin(self.base, f"{self.endpoint}/{id}")
        d = {
            "id": id,
            "name": name,
            "subject": subject,
            "lists": lists,
            "content_type": content_type,
            "type": type,
            "body": body,
            "body_source": body_source,
            "altbody": alt_body,
            "from_email": from_email,
            "messenger": messenger,
            "tags": tags,
            "send_at": send_at,
            "template_id": template_id,
            "headers": headers,
        }

        response = self.session.put(
            url, json={k: v for k, v in d.items() if v is not None}
        )
        data: CampaignContainer = cast(CampaignContainer, _handle_response(response))
        return data

    def update_status(
        self, id: int, status: Literal["scheduled", "draft", "paused", "running"]
    ) -> CampaignContainer:
        """
        See `PUT /api/campaigns/{id}/status https://listmonk.app/docs/apis/campaigns/#put-apicampaignscampaign_idstatus`_
        """
        url = urljoin(self.base, f"{self.endpoint}/{id}/status")
        d = {"status": status}
        response = self.session.put(url, json=d)
        data: CampaignContainer = cast(CampaignContainer, _handle_response(response))
        return data

    def delete(self, id: int) -> DeleteContainer:
        """
        See `DELETE /api/campaigns/{id} https://listmonk.app/docs/apis/campaigns/#delete-apicampaignscampaign_id`_
        """
        url = urljoin(self.base, f"{self.endpoint}/{id}")
        response = self.session.delete(url)
        data: DeleteContainer = cast(DeleteContainer, _handle_response(response))
        return data

    def send_test_email(
        self,
        id: int,
        subscribers: list[str],
        name: str,
        subject: str,
        lists: list[int],
        content_type: Literal["richtext", "html", "markdown", "plain", "visual"],
        type: Literal["optin", "regular"],
        body: str,
        body_source: Optional[str] = None,
        alt_body: Optional[str] = None,
        from_email: Optional[str] = None,
        messenger: Optional[str] = None,
        tags: Optional[list[str]] = None,
        send_at: Optional[str] = None,
        template_id: Optional[int] = None,
        headers: Optional[list[dict[str, str]]] = None,
    ) -> SendContainer:
        """
        See `POST /api/campaigns/{id}/test
        https://listmonk.app/docs/apis/campaigns/#post-apicampaignscampaign_idtest`_

        Parameters
        ----------
        subscribers: list[str]
            emails, e.g name@example.com
        """
        url = urljoin(self.base, f"{self.endpoint}/{id}/test")

        response = self.session.post(
            url,
            json={
                "id": id,
                "subscribers": subscribers,
                "name": name,
                "subject": subject,
                "lists": lists,
                "content_type": content_type,
                "type": type,
                "body": body,
                "body_source": body_source,
                "altbody": alt_body,
                "from_email": from_email,
                "messenger": messenger,
                "tags": tags,
                "send_at": send_at,
                "template_id": template_id,
                "headers": headers,
            },
        )
        data: SendContainer = cast(SendContainer, _handle_response(response))
        return data
