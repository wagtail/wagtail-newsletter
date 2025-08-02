import os

from datetime import datetime, timedelta, timezone

import pytest

from _utils import check_typed_dict
from conf import create_session, get_from_email, get_list_id, get_server_url

from wagtail_newsletter.campaign_backends.listmonk.api.campaigns import (
    AnalyticsContainer,
    APICampaigns,
    CampaignContainer,
    CampaignsContainer,
    DeleteContainer,
    SendContainer,
    StatsContainer,
)
from wagtail_newsletter.campaign_backends.listmonk.api.errors import APIClientError


pytestmark = pytest.mark.listmonk_integration


@pytest.fixture()
def campaigns() -> APICampaigns:
    session = create_session()
    c = APICampaigns(get_server_url(), session)
    return c


@pytest.fixture()
def test_email():
    email = os.environ.get("TEST_EMAIL")
    if not email:
        pytest.skip("TEST_EMAIL environment variable not set")
    return email


def test_get_campaigns(campaigns: APICampaigns):
    data = campaigns.get_campaigns()
    check_typed_dict(data, CampaignsContainer)


def _create(campaigns: APICampaigns):
    data = campaigns.create(
        name="Test Campaign",
        subject="Test Subject",
        lists=[get_list_id()],  # Get list ID from environment or default
        from_email=get_from_email(),
        content_type="html",
        messenger="email",
        type="regular",
        headers=[{"Content-Type": "application/json", "charset": "utf-8"}],
        body="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Email</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <p>This is a test campaign created by the automated tests.</p>
</body>
</html>
        """,
    )
    return data["data"]["id"]  # Return just the ID for easier use in tests


def _delete(campaigns: APICampaigns, id: int):
    """Delete a test campaign after tests"""
    try:
        campaigns.delete(id)
    except Exception as e:
        # Log but don't fail tests on cleanup error
        print(f"Warning: Failed to clean up test campaign {id}: {str(e)}")


@pytest.fixture()
def campaign_id(campaigns) -> int:
    """Create a test campaign and return its ID, cleaning up after the test"""
    id = _create(campaigns)
    yield id
    _delete(campaigns, id)


def test_create(campaigns: APICampaigns):
    data = campaigns.create(
        name="Create Test",
        subject="Create Test Subject",
        lists=[get_list_id()],
        from_email="My Newsletter <hello@example.com>",
        content_type="html",
        messenger="email",
        type="regular",
        headers=[{"Content-Type": "application/json", "charset": "utf-8"}],
        body="<html><body><h1>Create Test</h1></body></html>",
    )
    check_typed_dict(data, CampaignContainer)

    campaign_id = data["data"]["id"]
    _delete(campaigns, campaign_id)


def test_delete(campaigns: APICampaigns):
    campaign_id = _create(campaigns)
    data = campaigns.delete(campaign_id)
    check_typed_dict(data, DeleteContainer)


def test_get_campaign(campaigns: APICampaigns, campaign_id: int):
    data = campaigns.get_campaign(campaign_id)
    check_typed_dict(data, CampaignContainer)

    # Verify the campaign data is returned correctly
    assert data["data"]["id"] == campaign_id
    assert data["data"]["name"] is not None
    assert data["data"]["subject"] is not None


def test_update_campaign(campaigns: APICampaigns, campaign_id: int):
    """Test updating a campaign"""
    current = campaigns.get_campaign(campaign_id)["data"]

    updated_subject = "Updated Subject"

    update_params = {
        "id": current["id"],
        "name": current["name"],
        "subject": updated_subject,
        "lists": [item["id"] for item in current["lists"]],
        "content_type": current["content_type"],
        "type": current["type"],
        "body": current["body"],
        "body_source": current.get("body_source"),
        "alt_body": current.get("altbody"),
        "from_email": current["from_email"],
        "messenger": current["messenger"],
        "tags": current.get("tags", []),
        "template_id": current.get("template_id"),
    }

    if "headers" in current:
        update_params["headers"] = current["headers"]

    result = campaigns.update(**update_params)  # type: ignore

    check_typed_dict(result, CampaignContainer)

    updated = campaigns.get_campaign(campaign_id)["data"]
    assert updated["subject"] == updated_subject


def _create_non_existing_id(numbers: list[int]) -> int:
    if not numbers:
        return 0

    numbers_set = set(numbers)

    for i in range(len(numbers) + 1):
        if i not in numbers_set:
            return i

    return len(numbers)


def test_update_campaign_non_existing_id(campaigns: APICampaigns):
    data = campaigns.get_campaigns()
    ids = [el["id"] for el in data["data"]["results"]]
    id = _create_non_existing_id(ids)
    update_params = {
        "id": id,
        "name": "name",
        "subject": "Subject",
        "lists": [],
        "content_type": "html",
        "type": "public",
        "body": "<h1>Hello</h1>",
        "body_source": None,
        "alt_body": None,
        "from_email": "My Newsletter <hello@example.com>",
        "messenger": "email",
        "tags": [],
        "template_id": 1,
        "headers": [],
    }
    with pytest.raises(APIClientError) as error:
        campaigns.update(**update_params)
    assert error.value.status_code == 400
    assert error.value.text == "invalid ID"


def test_campaign_status(campaigns: APICampaigns, campaign_id: int):
    """Test changing campaign status"""
    current = campaigns.get_campaign(campaign_id)["data"]

    future_date = (datetime.now(tz=timezone.utc) + timedelta(hours=1)).isoformat(
        sep="T"
    )

    update_params = {
        "id": current["id"],
        "name": current["name"],
        "subject": current["subject"],
        "lists": [item["id"] for item in current["lists"]],
        "content_type": current["content_type"],
        "type": current["type"],
        "body": current["body"],
        "body_source": current.get("body_source"),
        "alt_body": current.get("altbody"),
        "from_email": current["from_email"],
        "messenger": current["messenger"],
        "tags": current.get("tags", []),
        "template_id": current.get("template_id"),
        "headers": current.get("headers", []),
        "send_at": future_date,
    }

    campaigns.update(**update_params)  # type: ignore

    result = campaigns.update_status(campaign_id, "scheduled")

    check_typed_dict(result, CampaignContainer)

    campaign = campaigns.get_campaign(campaign_id)["data"]
    assert campaign["status"] == "scheduled"

    campaigns.update_status(campaign_id, "draft")

    campaign = campaigns.get_campaign(campaign_id)["data"]
    assert campaign["status"] == "draft"


def test_analytics_endpoints(campaigns: APICampaigns, campaign_id: int):
    from_date = (datetime.now(tz=timezone.utc) - timedelta(days=30)).strftime(
        "%Y-%m-%d"
    )
    to_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

    for stat_type in ["views", "clicks", "bounces"]:
        result = campaigns.get_analytics(campaign_id, stat_type, from_date, to_date)  # type: ignore
        check_typed_dict(result, AnalyticsContainer)


def test_get_running_stats(campaigns: APICampaigns, campaign_id: int):
    stats = campaigns.get_running_stats(campaign_id)
    check_typed_dict(stats, StatsContainer)


@pytest.mark.mail
def test_send_test_email(
    request, campaigns: APICampaigns, campaign_id: int, test_email: str
):
    """Test sending a test email"""
    current = campaigns.get_campaign(campaign_id)["data"]

    # Use the same parameters as in the campaign, but add the test subscriber
    result = campaigns.send_test_email(
        id=current["id"],
        subscribers=[test_email],
        name=current["name"],
        subject="Test Email",
        lists=[item["id"] for item in current["lists"]],
        content_type=current["content_type"],
        type=current["type"],
        body=current["body"],
        body_source=current.get("body_source"),
        alt_body=current.get("altbody"),
        from_email=current["from_email"],
        messenger=current["messenger"],
        tags=current.get("tags", []),
        send_at=current.get("send_at"),
        template_id=current.get("template_id"),
        headers=current.get("headers", []),
    )
    check_typed_dict(result, SendContainer)
    assert result["data"] is True
    # NOTE: A passing test does not guarantee the email was successfully sent.
    # If the email specified in the from_email field of the campaign is not managed
    # by the SMTP server, the test will pass but the email may not actually be sent.
