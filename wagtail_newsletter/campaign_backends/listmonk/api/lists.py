from typing import Literal, Optional, TypedDict, cast
from urllib.parse import urljoin

import requests

from .errors import _handle_response


class SubscriptionList(TypedDict):
    id: int
    created_at: str
    updated_at: str
    uuid: str
    name: str
    type: str
    optin: str
    tags: list[str]
    subscriber_count: int
    description: str
    subscriber_statuses: dict[str, int]
    subscription_created_at: Optional[str]
    subscription_updated_at: Optional[str]


class Lists(TypedDict):
    results: list[SubscriptionList]
    search: str
    query: str
    total: int
    per_page: int
    page: int


class ListsContainer(TypedDict):
    data: Lists


class ListContainer(TypedDict):
    data: SubscriptionList


class DeleteContainer(TypedDict):
    data: bool


class APILists:
    """
    Interact with API endpoint `listmonk /api/lists https://listmonk.app/docs/apis/lists/`_
    """

    endpoint = "/api/lists"

    def __init__(self, base: str, session: requests.Session):
        self.base = base
        self.session = session

    @property
    def url(self) -> str:
        return urljoin(self.base, self.endpoint)

    def get_apilists(
        self,
        query: Optional[str] = None,
        status: Optional[list[str]] = None,
        tag: Optional[list[str]] = None,
        order_by: Optional[
            Literal["name", "status", "created_at", "updated_at"]
        ] = None,
        order: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[str | Literal["all"]] = None,
    ) -> ListsContainer:
        """
        See `GET /api/public/lists
        https://listmonk.app/docs/apis/lists/#get-apipubliclists`_
        """
        params = {
            "query": query,
            "status": status,
            "tag": tag,
            "order_by": order_by,
            "order": order,
            "page": page,
            "per_page": per_page,
        }
        response = self.session.get(
            self.url, params={k: v for k, v in params.items() if v is not None}
        )
        data: ListsContainer = cast(ListsContainer, _handle_response(response))
        return data

    def get_list_by_id(self, id: int) -> ListContainer:
        """
        See `GET /api/lists/{id} https://listmonk.app/docs/apis/lists/#get-apilistslist_id`_
        """
        endpoint = f"{self.endpoint}/{id}"
        url = urljoin(self.base, endpoint)
        response = self.session.get(url)
        data: ListContainer = cast(ListContainer, _handle_response(response))
        return data

    def create(
        self,
        name: str,
        type: Literal["public", "private"],
        optin: Literal["single", "double"],
        tags: Optional[list[str]] = None,
        description: Optional[str] = None,
    ) -> ListContainer:
        """
        See `POST apis/lists/ https://listmonk.app/docs/apis/lists/#post-apilists`_
        """
        d = {
            "name": name,
            "type": type,
            "optin": optin,
            "tags": tags,
            "description": description,
        }
        response = self.session.post(
            self.url, json={k: v for k, v in d.items() if v is not None}
        )
        data: ListContainer = cast(ListContainer, _handle_response(response))
        return data

    def update(
        self,
        id: int,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        uuid: Optional[str] = None,
        name: Optional[str] = None,
        type: Optional[str] = None,
        optin: Optional[str] = None,
        tags: Optional[list[str]] = None,
        subscriber_count: Optional[int] = None,
        description: Optional[str] = None,
    ) -> ListContainer:
        """
        See `PUT apis/lists/{id} https://listmonk.app/docs/apis/lists/#put-apilistslist_id`_
        """
        url = urljoin(self.base, f"{self.endpoint}/{id}")
        d = {
            "id": id,
            "created_at": created_at,
            "updated_at": updated_at,
            "uuid": uuid,
            "name": name,
            "type": type,
            "optin": optin,
            "tags": tags,
            "subscriber_count": subscriber_count,
            "description": description,
        }
        response = self.session.put(
            url, json={k: v for k, v in d.items() if v is not None}
        )
        data: ListContainer = cast(ListContainer, _handle_response(response))
        return data

    def delete(self, id: int) -> DeleteContainer:
        """
        See `DELETE apis/lists/{id} https://listmonk.app/docs/apis/lists/#delete-apilistslist_id`_
        """
        url = urljoin(self.base, f"{self.endpoint}/{id}")
        response = self.session.delete(url)
        data: DeleteContainer = cast(DeleteContainer, _handle_response(response))
        return data
