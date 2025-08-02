import pytest

from _utils import check_typed_dict
from conf import create_session, get_list_id, get_server_url

from wagtail_newsletter.campaign_backends.listmonk.api.lists import (
    APILists,
    DeleteContainer,
    ListContainer,
    ListsContainer,
)


pytestmark = pytest.mark.listmonk_integration


@pytest.fixture
def lists() -> APILists:
    """Create a lists API client for testing"""
    session = create_session()
    apilist = APILists(get_server_url(), session)
    return apilist


def test_get_apilists(lists: APILists):
    data = lists.get_apilists()

    check_typed_dict(data, ListsContainer)


def test_get_list_by_id(
    lists: APILists,
):
    id = get_list_id()
    data = lists.get_list_by_id(id)
    check_typed_dict(data, ListContainer)


def test_create_delete(lists: APILists):
    data = lists.create("Test list", "private", "single")
    check_typed_dict(data, ListContainer)
    list_id = data["data"]["id"]
    delete_data = lists.delete(list_id)
    check_typed_dict(delete_data, DeleteContainer)


def test_update(lists: APILists):
    create_data = lists.create("Test list", "private", "single")

    list_id = create_data["data"]["id"]
    newname = "Test List"
    data = lists.update(list_id, name=newname)
    check_typed_dict(data, ListContainer)
    assert data["data"]["name"] == newname
    list_id = data["data"]["id"]
    lists.delete(list_id)
