import logging

from datetime import datetime, timezone
from typing import Any, Optional
from unittest.mock import Mock, call

import pytest

from django.core.exceptions import ImproperlyConfigured

from wagtail_newsletter.audiences import Audience
from wagtail_newsletter.campaign_backends import CampaignBackendError
from wagtail_newsletter.campaign_backends.listmonk import (
    ListmonkCampaignBackend,
    _log_and_raise,
)
from wagtail_newsletter.campaign_backends.listmonk.api.errors import APIClientError
from wagtail_newsletter.test.models import CustomRecipients


WEB_BASE_URL = "http://localhost:9000"  # NOTE: SHould I move this ?
LIST_ID = 1
SUBJECT = "Test Subject"
HTML = "<h1>Test HTML</h1>"
CAMPAIGN_ID = "1"
NEW_CAMPAIGN_ID = "2"
EMAIL = "test@example.com"
API_ERROR_TEXT = '{"message": "invalid ID"}'
SCHEDULE_TIME = datetime(2024, 8, 10, 16, 30, tzinfo=timezone.utc)


class MockListmonkCampaignBackend(ListmonkCampaignBackend):
    def __init__(self):
        self.client: Mock = Mock()  # type: ignore


@pytest.fixture
def backend():
    return MockListmonkCampaignBackend()


def _mock_data(
    campaign_id: str,
    status: str,
    list_ids: list[int],
    views: int = 0,
    clicks: int = 0,
    bounces: int = 0,
    sent: int = 0,
    send_at: Optional[str] = None,
):
    return {
        "data": {
            "id": int(campaign_id),
            "created_at": "2021-12-27T00:00:00.333485Z",
            "updated_at": "2021-12-27T00:00:00.333485Z",
            "views": views,
            "clicks": clicks,
            "bounces": bounces,
            "lists": [
                {"id": list_id, "name": f"list {list_id}"} for list_id in list_ids
            ],
            "started_at": None,
            "to_send": 1,
            "sent": sent,
            "uuid": "odiwh",
            "type": "regular",
            "name": "Name",
            "subject": SUBJECT,
            "from_email": EMAIL,
            "body": HTML,
            "body_source": None,
            "altbody": None,
            "send_at": send_at,
            "status": status,
            "content_type": "html",
            "tags": [],
            "template_id": 1,
            "messenger": "email",
            "media": [],
            "headers": [],
            "archive": False,
            "archive_meta": {},
            "archive_slug": None,
            "archive_template_id": None,
        }
    }


def test_configure_client(settings):
    settings.WAGTAIL_NEWSLETTER_LISTMONK_API_KEY = "..."
    settings.WAGTAIL_NEWSLETTER_LISTMONK_USER = "..."
    settings.WAGTAIL_NEWSLETTER_LISTMONK_BASE_URL = "http://localhost:9000"
    backend = ListmonkCampaignBackend()
    assert backend.client.base == "http://localhost:9000"


def test_no_api_key(settings):
    settings.WAGTAIL_NEWSLETTER_LISTMONK_API_KEY = None
    settings.WAGTAIL_NEWSLETTER_LISTMONK_USER = "..."
    settings.WAGTAIL_NEWSLETTER_LISTMONK_BASE_URL = "http://localhost:9000"

    with pytest.raises(ImproperlyConfigured) as error:
        ListmonkCampaignBackend().client  # noqa: B018

    assert error.match(r"WAGTAIL_NEWSLETTER_LISTMONK_API_KEY is not set")


def test_no_api_user(settings):
    settings.WAGTAIL_NEWSLETTER_LISTMONK_API_KEY = "..."
    settings.WAGTAIL_NEWSLETTER_LISTMONK_USER = None
    settings.WAGTAIL_NEWSLETTER_LISTMONK_BASE_URL = "http://localhost:9000"
    with pytest.raises(ImproperlyConfigured) as error:
        ListmonkCampaignBackend().client  # noqa: B018

    assert error.match(r"WAGTAIL_NEWSLETTER_LISTMONK_USER is not set")


def test_no_api_base(settings):
    settings.WAGTAIL_NEWSLETTER_LISTMONK_API_KEY = "..."
    settings.WAGTAIL_NEWSLETTER_LISTMONK_USER = "..."
    settings.WAGTAIL_NEWSLETTER_LISTMONK_BASE_URL = None
    with pytest.raises(ImproperlyConfigured) as error:
        ListmonkCampaignBackend().client  # noqa: B018

    assert error.match(r"WAGTAIL_NEWSLETTER_LISTMONK_BASE_URL is not set")


def test_get_audiences(backend: MockListmonkCampaignBackend):
    backend.client.lists.get_apilists.return_value = {
        "data": {
            "results": [
                {
                    "id": 1,
                    "created_at": "2020-02-10T00:00:00.194843+01:00",
                    "updated_at": "2020-03-06T00:00:00.118327+01:00",
                    "uuid": "anuuid",
                    "name": "Default List",
                    "type": "public",
                    "optin": "double",
                    "tags": ["test"],
                    "description": "",
                    "subscriber_statuses": {"1": 1},
                    "subscriber_count": 2,
                    "subscription_created_at": "2020-04-14T00:00:00.29451+01:00",
                    "subscription_updated_at": "2020-04-14T00:00:00.29451+01:00",
                },
                {
                    "id": 2,
                    "created_at": "2020-02-10T00:00:00.194843+01:00",
                    "updated_at": "2020-03-06T00:00:00.118327+01:00",
                    "uuid": "anuuid",
                    "name": "Second List",
                    "type": "private",
                    "optin": "double",
                    "tags": ["test"],
                    "description": "",
                    "subscriber_count": 3,
                    "subscriber_statuses": {"1": 1},
                    "subscription_created_at": "2020-04-14T00:00:00.29451+01:00",
                    "subscription_updated_at": "2020-04-14T00:00:00.29451+01:00",
                },
            ],
        }
    }

    assert backend.get_audiences() == [
        Audience(id=1, name="Default List", member_count=2),
        Audience(id=2, name="Second List", member_count=3),
    ]


def test_get_audience_segments(backend: MockListmonkCampaignBackend):
    with pytest.raises(Audience.DoesNotExist):
        backend.get_audience_segments("id")


@pytest.mark.parametrize(
    "recipients_object,recipients_data",
    [
        (None, []),
        (CustomRecipients(audience=LIST_ID), [LIST_ID]),
    ],
)
def test_create_campaign(
    backend: MockListmonkCampaignBackend,
    settings,
    recipients_object,
    recipients_data,
):
    backend.client.campaigns.create.return_value = _mock_data(
        CAMPAIGN_ID, "draft", recipients_data
    )
    name = "name"

    assert (
        backend.save_campaign(
            name=name,
            recipients=recipients_object,
            subject=SUBJECT,
            html=HTML,
        )
        == CAMPAIGN_ID
    )
    mail_name = settings.WAGTAIL_NEWSLETTER_FROM_NAME
    mail_address = settings.WAGTAIL_NEWSLETTER_REPLY_TO
    from_email = f"{mail_name} <{mail_address}>"

    assert backend.client.campaigns.create.mock_calls == [
        call(
            name=name,
            subject=SUBJECT,
            lists=recipients_data,
            content_type="html",
            type="regular",
            body=HTML,
            from_email=from_email,
            headers=[{"Content-Type": "application/json", "charset": "utf-8"}],
            messenger="email",
        )
    ]


def test_create_campaign_handle_create_exception(backend: ListmonkCampaignBackend):
    backend.client.campaigns.create.side_effect = APIClientError("", 400)

    with pytest.raises(CampaignBackendError) as error:
        backend.save_campaign(
            name="name",
            recipients=None,
            subject="Test Subject",
            html="<h1>Test HTML</h1>",
        )

    assert error.match(r"Error while creating campaign")


@pytest.mark.parametrize(
    "recipients_object,recipients_data",
    [
        (None, []),
        (CustomRecipients(audience=LIST_ID), [LIST_ID]),
    ],
)
def test_update_campaign(
    backend: MockListmonkCampaignBackend,
    settings,
    recipients_object,
    recipients_data,
):
    backend.client.campaigns.update.return_value = _mock_data(
        CAMPAIGN_ID, "draft", recipients_data
    )
    name = "name"
    campaign_id = backend.save_campaign(
        name=name,
        campaign_id=CAMPAIGN_ID,
        recipients=recipients_object,
        subject=SUBJECT,
        html=HTML,
    )
    assert campaign_id == CAMPAIGN_ID
    mail_name = settings.WAGTAIL_NEWSLETTER_FROM_NAME
    mail_address = settings.WAGTAIL_NEWSLETTER_REPLY_TO
    from_email = f"{mail_name} <{mail_address}>"

    assert backend.client.campaigns.update.mock_calls == [
        call(
            id=int(CAMPAIGN_ID),
            name=name,
            subject=SUBJECT,
            lists=recipients_data,
            content_type="html",
            type="regular",
            body=HTML,
            from_email=from_email,
            headers=[{"Content-Type": "application/json", "charset": "utf-8"}],
            messenger="email",
        ),
    ]


def test_update_campaign_not_found(backend: MockListmonkCampaignBackend, settings):
    backend.client.campaigns.update.side_effect = APIClientError(API_ERROR_TEXT, 400)

    backend.client.campaigns.create.return_value = {
        "data": {
            "id": int(NEW_CAMPAIGN_ID),
            "created_at": "2021-12-27T00:00:00.333485Z",
            "updated_at": "2021-12-27T00:00:00.333485Z",
            "views": 0,
            "clicks": 0,
            "bounces": 0,
            "lists": [{"id": LIST_ID, "name": f"list {LIST_ID}"}],
            "started_at": None,
            "to_send": 1,
            "sent": 0,
            "uuid": "odiwh",
            "type": "regular",
            "name": "Name",
            "subject": "Subject",
            "from_email": EMAIL,
            "body": HTML,
            "body_source": None,
            "altbody": None,
            "send_at": None,
            "status": "draft",
            "content_type": "html",
            "tags": [],
            "template_id": 1,
            "messenger": "email",
            "media": [],
            "headers": [],
            "archive": False,
            "archive_meta": {},
            "archive_slug": None,
            "archive_template_id": None,
        }
    }
    name = "name"

    campaign_id = backend.save_campaign(
        name=name,
        campaign_id=CAMPAIGN_ID,
        recipients=CustomRecipients(audience=LIST_ID),
        subject=SUBJECT,
        html=HTML,
    )
    mail_name = settings.WAGTAIL_NEWSLETTER_FROM_NAME
    mail_address = settings.WAGTAIL_NEWSLETTER_REPLY_TO
    from_email = f"{mail_name} <{mail_address}>"

    assert campaign_id == NEW_CAMPAIGN_ID

    assert backend.client.campaigns.update.mock_calls == [
        call(
            id=int(CAMPAIGN_ID),
            name=name,
            subject=SUBJECT,
            lists=[LIST_ID],
            content_type="html",
            type="regular",
            body=HTML,
            from_email=from_email,
            headers=[{"Content-Type": "application/json", "charset": "utf-8"}],
            messenger="email",
        ),
    ]
    assert backend.client.campaigns.create.mock_calls == [
        call(
            name=name,
            subject=SUBJECT,
            lists=[LIST_ID],
            content_type="html",
            type="regular",
            body=HTML,
            from_email=from_email,
            headers=[{"Content-Type": "application/json", "charset": "utf-8"}],
            messenger="email",
        )
    ]


def test_update_campaign_handle_update_exception(backend: MockListmonkCampaignBackend):
    backend.client.campaigns.update.side_effect = APIClientError("", 400)

    with pytest.raises(CampaignBackendError) as error:
        backend.save_campaign(
            name="name",
            campaign_id=CAMPAIGN_ID,
            recipients=None,
            subject="Test Subject",
            html="<h1>Test HTML</h1>",
        )

    assert error.match(r"Error while updating campaign")


@pytest.mark.parametrize(
    "data,is_scheduled,is_sent,url",
    [
        (
            _mock_data(CAMPAIGN_ID, "draft", [LIST_ID]),
            False,
            False,
            f"{WEB_BASE_URL}/api/campaigns/{CAMPAIGN_ID}",
        ),
        (
            _mock_data(CAMPAIGN_ID, "scheduled", [LIST_ID]),
            True,
            False,
            f"{WEB_BASE_URL}/api/campaigns/{CAMPAIGN_ID}",
        ),
        (
            _mock_data(CAMPAIGN_ID, "paused", [LIST_ID]),
            False,
            False,
            f"{WEB_BASE_URL}/api/campaigns/{CAMPAIGN_ID}",
        ),
        (
            _mock_data(CAMPAIGN_ID, "running", [LIST_ID]),
            False,
            True,
            f"{WEB_BASE_URL}/api/campaigns/{CAMPAIGN_ID}",
        ),
    ],
)
def test_get_campaign(
    backend: MockListmonkCampaignBackend, data, is_scheduled, is_sent, url
):
    backend.client.campaigns.get_campaign.return_value = data
    backend.client.campaigns.url = f"{WEB_BASE_URL}/api/campaigns"
    campaign = backend.get_campaign(CAMPAIGN_ID)
    assert campaign is not None
    assert backend.client.campaigns.get_campaign.mock_calls == [call(int(CAMPAIGN_ID))]
    assert campaign.is_scheduled == is_scheduled
    assert campaign.is_sent == is_sent
    assert campaign.url == url


def test_get_campaign_not_found(backend: MockListmonkCampaignBackend):
    backend.client.campaigns.get_campaign.side_effect = APIClientError(
        API_ERROR_TEXT, 400
    )
    assert backend.get_campaign("1000") is None


def test_get_campaign_handle_exception(backend: MockListmonkCampaignBackend):
    backend.client.campaigns.get_campaign.side_effect = APIClientError("", 400)
    with pytest.raises(CampaignBackendError) as error:
        backend.get_campaign(CAMPAIGN_ID)

    assert error.match("Error while fetching campaign")


@pytest.mark.parametrize("send_completed", [True, False])
def test_campaign_report(backend: ListmonkCampaignBackend, send_completed: bool):
    backend.client.campaigns.get_campaign.return_value = _mock_data(
        CAMPAIGN_ID,
        "running",
        [LIST_ID],
        bounces=6,
        views=5,
        clicks=3,
        sent=13,
        send_at="2024-06-17T12:51:46+00:00" if send_completed else None,
    )
    expected: dict[str, Any] = {
        "bounces": 6,
        "clicks": 3,
        "emails_sent": 13,
        "opens": 5,
    }
    if send_completed:
        expected["send_time"] = datetime(2024, 6, 17, 12, 51, 46, tzinfo=timezone.utc)

    campaign = backend.get_campaign(CAMPAIGN_ID)
    assert campaign is not None
    report = campaign.get_report()
    assert report == expected


def test_log_and_raise(caplog: pytest.LogCaptureFixture):
    MESSAGE = "Message for testing"
    TEST_VALUE = "test-value"

    with caplog.at_level(logging.ERROR, "wagtail_newsletter"):
        with pytest.raises(CampaignBackendError) as error:
            _log_and_raise(
                APIClientError(API_ERROR_TEXT, 400),
                MESSAGE,
                test_key=TEST_VALUE,
            )

    assert error.match(MESSAGE)
    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    assert f"test_key={TEST_VALUE!r}" in log_record.message
    assert "status_code=400" in log_record.message
    assert "text='invalid ID'" in log_record.message


def test_send_test_email(backend: MockListmonkCampaignBackend):
    backend.client.campaigns.get_campaign.return_value = _mock_data(
        CAMPAIGN_ID, "draft", [LIST_ID]
    )
    backend.client.campaigns.send_test_email.return_value = {"data": True}

    backend.send_test_email(campaign_id=CAMPAIGN_ID, email=EMAIL)

    assert backend.client.campaigns.send_test_email.mock_calls == [
        call(
            id=int(CAMPAIGN_ID),
            subscribers=[EMAIL],
            name="Name",
            subject=SUBJECT,
            lists=[LIST_ID],
            content_type="html",
            type="regular",
            body=HTML,
            body_source=None,
            alt_body=None,
            from_email=EMAIL,
            messenger="email",
            tags=[],
            send_at=None,
            template_id=1,
            headers=[],
        )
    ]


def test_send_test_email_failure(backend: MockListmonkCampaignBackend):
    backend.client.campaigns.get_campaign.return_value = _mock_data(
        CAMPAIGN_ID, "draft", [LIST_ID]
    )

    backend.client.campaigns.send_test_email.side_effect = APIClientError("", 400)
    with pytest.raises(CampaignBackendError) as error:
        backend.send_test_email(campaign_id=CAMPAIGN_ID, email=EMAIL)

    assert error.match("Error while sending test email")


def test_send_test_email_data_failure(backend: MockListmonkCampaignBackend):
    backend.client.campaigns.get_campaign.return_value = _mock_data(
        CAMPAIGN_ID, "draft", [LIST_ID]
    )

    backend.client.campaigns.send_test_email.return_value = {"data": False}
    with pytest.raises(CampaignBackendError) as error:
        backend.send_test_email(campaign_id=CAMPAIGN_ID, email=EMAIL)

    assert error.match("Error while sending test email")


def test_send_campaign(backend: MockListmonkCampaignBackend):
    backend.send_campaign(CAMPAIGN_ID)
    assert backend.client.campaigns.update_status.mock_calls == [
        call(id=int(CAMPAIGN_ID), status="running")
    ]


def test_send_campaign_failure(backend: MockListmonkCampaignBackend):
    backend.client.campaigns.update_status.side_effect = APIClientError(
        API_ERROR_TEXT, 400
    )
    with pytest.raises(CampaignBackendError) as error:
        backend.send_campaign(campaign_id=CAMPAIGN_ID)

    assert error.match("Error while sending campaign")


def test_schedule_campaign(backend: MockListmonkCampaignBackend):
    backend.client.campaigns.get_campaign.return_value = _mock_data(
        CAMPAIGN_ID, "draft", [LIST_ID]
    )
    backend.client.campaigns.update.return_value = _mock_data(
        CAMPAIGN_ID, "draft", [LIST_ID], send_at=SCHEDULE_TIME.isoformat()
    )

    backend.schedule_campaign(CAMPAIGN_ID, SCHEDULE_TIME)
    assert backend.client.campaigns.update_status.mock_calls == [
        call(id=int(CAMPAIGN_ID), status="scheduled")
    ]


def test_schedule_campaign_failure(backend: ListmonkCampaignBackend):
    backend.client.campaigns.get_campaign.return_value = _mock_data(
        CAMPAIGN_ID, "draft", [LIST_ID]
    )
    backend.client.campaigns.update.return_value = _mock_data(
        CAMPAIGN_ID, "draft", [LIST_ID], send_at=SCHEDULE_TIME.isoformat()
    )
    backend.client.campaigns.update_status.side_effect = APIClientError("", 400)
    with pytest.raises(CampaignBackendError) as error:
        backend.schedule_campaign(CAMPAIGN_ID, SCHEDULE_TIME)

    assert error.match("Error while scheduling campaign")


def test_unschedule_campaign(backend: MockListmonkCampaignBackend):
    backend.unschedule_campaign(CAMPAIGN_ID)
    assert backend.client.campaigns.update_status.mock_calls == [
        call(id=int(CAMPAIGN_ID), status="draft")
    ]


def test_unschedule_campaign_failure(backend: MockListmonkCampaignBackend):
    backend.client.campaigns.update_status.side_effect = APIClientError("", 400)
    with pytest.raises(CampaignBackendError) as error:
        backend.unschedule_campaign(CAMPAIGN_ID)

    assert error.match("Error while unscheduling campaign")
