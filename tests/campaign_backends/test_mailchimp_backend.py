import logging

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import ANY, Mock, call

import pytest

from django.core.exceptions import ImproperlyConfigured
from mailchimp_marketing.api_client import ApiClientError

from wagtail_newsletter.audiences import (
    Audience,
    AudienceSegment,
)
from wagtail_newsletter.campaign_backends import CampaignBackendError
from wagtail_newsletter.campaign_backends.mailchimp import (
    MailchimpCampaignBackend,
    _log_and_raise,
)
from wagtail_newsletter.test.models import CustomRecipients


WEB_SERVER = "mock-server"
WEB_BASE_URL = f"https://{WEB_SERVER}.admin.mailchimp.com"
LIST_ID = "test-audience-id"
SEGMENT_ID = 12345
SUBJECT = "Test Subject"
HTML = "<h1>Test HTML</h1>"
CAMPAIGN_ID = "test-campaign-id"
CAMPAIGN_WEB_ID = "test-web-id"
NEW_CAMPAIGN_ID = "test-new-campaign-id"
API_ERROR_TEXT = "something failed"
EMAIL = "test@example.com"
SCHEDULE_TIME = datetime(2024, 8, 10, 16, 30, tzinfo=timezone.utc)


class MockMailchimpCampaignBackend(MailchimpCampaignBackend):
    def __init__(self):
        self.client: Mock = Mock()  # type: ignore


@pytest.fixture
def backend():
    return MockMailchimpCampaignBackend()


def test_configure_client(settings):
    settings.WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY = (
        "00000000000000000000000000000000-us13"
    )
    backend = MailchimpCampaignBackend()
    assert backend.client.api_client.server == "us13"


def test_no_api_key(settings):
    settings.WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY = None
    with pytest.raises(ImproperlyConfigured) as error:
        MailchimpCampaignBackend().client  # noqa: B018

    assert error.match(r"WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY is not set")


def test_get_audiences(backend: MockMailchimpCampaignBackend):
    backend.client.lists.get_all_lists.return_value = {
        "lists": [
            {"id": "be13e6ca91", "name": "Torchbox", "stats": {"member_count": 8}},
            {"id": "9af08f2afa", "name": "Other", "stats": {"member_count": 13}},
        ],
    }

    assert backend.get_audiences() == [
        Audience(id="be13e6ca91", name="Torchbox", member_count=8),
        Audience(id="9af08f2afa", name="Other", member_count=13),
    ]


def test_get_audience_segments(backend: MockMailchimpCampaignBackend):
    backend.client.lists.list_segments.return_value = {
        "list_id": "be13e6ca91",
        "segments": [
            {"id": 2103836, "member_count": 3, "name": "Segment One"},
            {"id": 2103837, "member_count": 1, "name": "Segment Two"},
            {"id": 2103838, "member_count": 1, "name": "Segment Three"},
        ],
    }

    assert backend.get_audience_segments("be13e6ca91") == [
        AudienceSegment(id="be13e6ca91/2103836", name="Segment One", member_count=3),
        AudienceSegment(id="be13e6ca91/2103837", name="Segment Two", member_count=1),
        AudienceSegment(id="be13e6ca91/2103838", name="Segment Three", member_count=1),
    ]


def test_get_audience_segments_list_not_found(backend: MockMailchimpCampaignBackend):
    backend.client.lists.list_segments.side_effect = ApiClientError("", 404)

    with pytest.raises(Audience.DoesNotExist):
        backend.get_audience_segments("be13e6ca91")


def test_get_audience_segments_api_error(backend: MockMailchimpCampaignBackend):
    backend.client.lists.list_segments.side_effect = ApiClientError("", 400)

    with pytest.raises(CampaignBackendError) as error:
        backend.get_audience_segments("be13e6ca91")

    assert error.match(r"Error while fetching audience segments")


@pytest.mark.parametrize(
    "recipients_object,recipients_data",
    [
        (None, None),
        (CustomRecipients(audience=LIST_ID), {"list_id": LIST_ID}),
        (
            CustomRecipients(audience=LIST_ID, segment=f"{LIST_ID}/{SEGMENT_ID}"),
            {"list_id": LIST_ID, "segment_opts": {"saved_segment_id": SEGMENT_ID}},
        ),
    ],
)
def test_create_campaign(
    backend: MockMailchimpCampaignBackend,
    settings,
    recipients_object,
    recipients_data,
):
    backend.client.campaigns.create.return_value = {"id": CAMPAIGN_ID}

    assert (
        backend.save_campaign(
            recipients=recipients_object,
            subject=SUBJECT,
            html=HTML,
        )
        == CAMPAIGN_ID
    )

    expected_body = {
        **({"recipients": recipients_data} if recipients_data else {}),
        "settings": {
            "from_name": settings.WAGTAIL_NEWSLETTER_FROM_NAME,
            "reply_to": settings.WAGTAIL_NEWSLETTER_REPLY_TO,
            "subject_line": SUBJECT,
        },
        "type": "regular",
    }
    assert backend.client.campaigns.create.mock_calls == [call(expected_body)]
    assert backend.client.campaigns.set_content.mock_calls == [
        call(CAMPAIGN_ID, {"html": HTML}),
    ]


def test_create_campaign_handle_create_exception(backend: MockMailchimpCampaignBackend):
    backend.client.campaigns.create.side_effect = ApiClientError("", 400)

    with pytest.raises(CampaignBackendError) as error:
        backend.save_campaign(
            recipients=None,
            subject="Test Subject",
            html="<h1>Test HTML</h1>",
        )

    assert error.match(r"Error while creating campaign")


def test_create_campaign_handle_content_exception(
    backend: MockMailchimpCampaignBackend,
):
    backend.client.campaigns.create.return_value = {"id": "test-campaign-id"}
    backend.client.campaigns.set_content.side_effect = ApiClientError("", 400)

    with pytest.raises(CampaignBackendError) as error:
        backend.save_campaign(
            recipients=None,
            subject="Test Subject",
            html="<h1>Test HTML</h1>",
        )

    assert error.match(r"Error while saving campaign content")


@pytest.mark.parametrize(
    "recipients_object,recipients_data",
    [
        (None, None),
        (CustomRecipients(audience=LIST_ID), {"list_id": LIST_ID}),
        (
            CustomRecipients(audience=LIST_ID, segment=f"{LIST_ID}/{SEGMENT_ID}"),
            {"list_id": LIST_ID, "segment_opts": {"saved_segment_id": SEGMENT_ID}},
        ),
    ],
)
def test_update_campaign(
    backend: MockMailchimpCampaignBackend,
    settings,
    recipients_object,
    recipients_data,
):
    campaign_id = backend.save_campaign(
        campaign_id=CAMPAIGN_ID,
        recipients=recipients_object,
        subject=SUBJECT,
        html=HTML,
    )
    assert campaign_id == CAMPAIGN_ID

    expected_body = {
        **({"recipients": recipients_data} if recipients_data else {}),
        "settings": {
            "from_name": settings.WAGTAIL_NEWSLETTER_FROM_NAME,
            "reply_to": settings.WAGTAIL_NEWSLETTER_REPLY_TO,
            "subject_line": SUBJECT,
        },
    }
    assert backend.client.campaigns.update.mock_calls == [
        call(CAMPAIGN_ID, expected_body),
    ]
    assert backend.client.campaigns.set_content.mock_calls == [
        call(CAMPAIGN_ID, {"html": HTML}),
    ]


def test_update_campaign_not_found(backend: MockMailchimpCampaignBackend, settings):
    """
    If the campaign has been deleted on the Mailchimp end, we need to create a new one,
    and return its ID.
    """

    backend.client.campaigns.update.side_effect = ApiClientError("", 404)
    backend.client.campaigns.create.return_value = {"id": NEW_CAMPAIGN_ID}

    campaign_id = backend.save_campaign(
        campaign_id=CAMPAIGN_ID,
        recipients=CustomRecipients(audience=LIST_ID),
        subject=SUBJECT,
        html=HTML,
    )
    assert campaign_id == NEW_CAMPAIGN_ID

    expected_body = {
        "recipients": {
            "list_id": LIST_ID,
        },
        "settings": {
            "from_name": settings.WAGTAIL_NEWSLETTER_FROM_NAME,
            "reply_to": settings.WAGTAIL_NEWSLETTER_REPLY_TO,
            "subject_line": SUBJECT,
        },
    }
    assert backend.client.campaigns.update.mock_calls == [
        call(CAMPAIGN_ID, expected_body),
    ]
    assert backend.client.campaigns.create.mock_calls == [
        call({**expected_body, "type": "regular"}),
    ]
    assert backend.client.campaigns.set_content.mock_calls == [
        call(NEW_CAMPAIGN_ID, {"html": HTML}),
    ]


def test_update_campaign_handle_update_exception(backend: MockMailchimpCampaignBackend):
    backend.client.campaigns.update.side_effect = ApiClientError("", 400)

    with pytest.raises(CampaignBackendError) as error:
        backend.save_campaign(
            campaign_id="test-campaign-id",
            recipients=None,
            subject="Test Subject",
            html="<h1>Test HTML</h1>",
        )

    assert error.match(r"Error while updating campaign")


@pytest.mark.parametrize(
    "data,is_scheduled,is_sent,url",
    [
        (
            {"web_id": CAMPAIGN_WEB_ID, "status": "save"},
            False,
            False,
            f"{WEB_BASE_URL}/campaigns/edit?id={CAMPAIGN_WEB_ID}",
        ),
        (
            {"web_id": CAMPAIGN_WEB_ID, "status": "schedule"},
            True,
            False,
            f"{WEB_BASE_URL}/campaigns/edit?id={CAMPAIGN_WEB_ID}",
        ),
        (
            {"web_id": CAMPAIGN_WEB_ID, "status": "paused"},
            False,
            False,
            f"{WEB_BASE_URL}/campaigns/edit?id={CAMPAIGN_WEB_ID}",
        ),
        (
            {"web_id": CAMPAIGN_WEB_ID, "status": "sent"},
            False,
            True,
            f"{WEB_BASE_URL}/reports/summary?id={CAMPAIGN_WEB_ID}",
        ),
    ],
)
def test_get_campaign(
    backend: MockMailchimpCampaignBackend, data, is_scheduled, is_sent, url
):
    backend.client.campaigns.get.return_value = data
    backend.client.api_client.server = WEB_SERVER
    campaign = backend.get_campaign(CAMPAIGN_ID)
    assert campaign is not None
    assert backend.client.campaigns.get.mock_calls == [call(CAMPAIGN_ID)]
    assert campaign.is_scheduled == is_scheduled
    assert campaign.is_sent == is_sent
    assert campaign.url == url


def test_get_campaign_not_found(backend: MockMailchimpCampaignBackend):
    backend.client.campaigns.get.side_effect = ApiClientError("", 404)
    assert backend.get_campaign("test-campaign-id") is None


def test_get_campaign_handle_exception(backend: MockMailchimpCampaignBackend):
    backend.client.campaigns.get.side_effect = ApiClientError(API_ERROR_TEXT, 400)
    with pytest.raises(CampaignBackendError) as error:
        backend.get_campaign(CAMPAIGN_ID)

    assert error.match("Error while fetching campaign")


@pytest.mark.parametrize("send_completed", [True, False])
def test_campaign_report(backend: MockMailchimpCampaignBackend, send_completed: bool):
    backend.client.campaigns.get.return_value = {
        "web_id": CAMPAIGN_WEB_ID,
        "status": "sent",
    }
    backend.client.reports.get_campaign_report.return_value = {
        "emails_sent": 13,
        "bounces": {"hard_bounces": 1, "soft_bounces": 2, "syntax_errors": 3},
        "opens": {"unique_opens": 5},
        "clicks": {"unique_clicks": 3},
        "send_time": None,
    }
    expected: dict[str, Any] = {
        "bounces": 6,
        "clicks": 3,
        "emails_sent": 13,
        "opens": 5,
    }
    if send_completed:
        backend.client.reports.get_campaign_report.return_value["send_time"] = (
            "2024-06-17T12:51:46+00:00"
        )
        expected["send_time"] = datetime(2024, 6, 17, 12, 51, 46, tzinfo=timezone.utc)

    campaign = backend.get_campaign(CAMPAIGN_ID)
    assert campaign is not None
    report = campaign.get_report()
    assert report == expected


def test_campaign_report_handle_exception(backend: MockMailchimpCampaignBackend):
    backend.client.campaigns.get.return_value = {
        "web_id": CAMPAIGN_WEB_ID,
        "status": "sent",
    }
    backend.client.reports.get_campaign_report.side_effect = ApiClientError("", 400)
    campaign = backend.get_campaign(CAMPAIGN_ID)
    assert campaign is not None
    with pytest.raises(CampaignBackendError) as error:
        campaign.get_report()

    assert error.match("Error while fetching campaign report")


def test_log_and_raise(caplog: pytest.LogCaptureFixture):
    MESSAGE = "Message for testing"
    TEST_VALUE = "test-value"

    with caplog.at_level(logging.ERROR, "wagtail_newsletter"):
        with pytest.raises(CampaignBackendError) as error:
            _log_and_raise(
                ApiClientError(API_ERROR_TEXT, 400),
                MESSAGE,
                test_key=TEST_VALUE,
            )

    assert error.match(MESSAGE)

    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    assert f"test_key={TEST_VALUE!r}" in log_record.message
    assert "status_code=400" in log_record.message
    assert f"text={API_ERROR_TEXT!r}" in log_record.message


def test_inject_campaign_settings():
    class InjectBackend(MockMailchimpCampaignBackend):
        def get_campaign_request_body(self, *, recipients, subject):
            return dict(
                super().get_campaign_request_body(
                    recipients=recipients, subject=subject
                ),
                test_key="test_value",
            )

    backend = InjectBackend()
    backend.client.campaigns.create.return_value = {"id": "test-campaign-id"}
    backend.save_campaign(
        recipients=None,
        subject="Test Subject",
        html="<h1>Test HTML</h1>",
    )

    expected_body = {
        "settings": ANY,
        "test_key": "test_value",
        "type": "regular",
    }
    assert backend.client.campaigns.create.mock_calls == [call(expected_body)]


def test_send_test_email(backend: MockMailchimpCampaignBackend):
    backend.send_test_email(campaign_id=CAMPAIGN_ID, email=EMAIL)
    assert backend.client.campaigns.send_test_email.mock_calls == [
        call(CAMPAIGN_ID, {"test_emails": [EMAIL], "send_type": "html"})
    ]


def test_send_test_email_failure(backend: MockMailchimpCampaignBackend):
    backend.client.campaigns.send_test_email.side_effect = ApiClientError("", 400)
    with pytest.raises(CampaignBackendError) as error:
        backend.send_test_email(campaign_id=CAMPAIGN_ID, email=EMAIL)

    assert error.match("Error while sending test email")


def test_send_campaign(backend: MockMailchimpCampaignBackend):
    backend.send_campaign(CAMPAIGN_ID)
    assert backend.client.campaigns.send.mock_calls == [call(CAMPAIGN_ID)]


def test_send_campaign_failure(backend: MockMailchimpCampaignBackend):
    backend.client.campaigns.send.side_effect = ApiClientError("", 400)
    with pytest.raises(CampaignBackendError) as error:
        backend.send_campaign(campaign_id=CAMPAIGN_ID)

    assert error.match("Error while sending campaign")


def test_schedule_campaign(backend: MockMailchimpCampaignBackend):
    backend.schedule_campaign(CAMPAIGN_ID, SCHEDULE_TIME)
    assert backend.client.campaigns.schedule.mock_calls == [
        call(CAMPAIGN_ID, {"schedule_time": SCHEDULE_TIME.isoformat()})
    ]


def test_schedule_campaign_failure(backend: MockMailchimpCampaignBackend):
    backend.client.campaigns.schedule.side_effect = ApiClientError("", 400)
    with pytest.raises(CampaignBackendError) as error:
        backend.schedule_campaign(CAMPAIGN_ID, SCHEDULE_TIME)

    assert error.match("Error while scheduling campaign")


def test_schedule_campaign_invalid_time(backend: MockMailchimpCampaignBackend):
    with pytest.raises(CampaignBackendError) as error:
        backend.schedule_campaign(CAMPAIGN_ID, SCHEDULE_TIME + timedelta(minutes=1))

    assert error.match("Schedule time must be in 15 minute intervals")


def test_unschedule_campaign(backend: MockMailchimpCampaignBackend):
    backend.unschedule_campaign(CAMPAIGN_ID)
    assert backend.client.campaigns.unschedule.mock_calls == [call(CAMPAIGN_ID)]


def test_unschedule_campaign_failure(backend: MockMailchimpCampaignBackend):
    backend.client.campaigns.unschedule.side_effect = ApiClientError("", 400)
    with pytest.raises(CampaignBackendError) as error:
        backend.unschedule_campaign(CAMPAIGN_ID)

    assert error.match("Error while unscheduling campaign")
