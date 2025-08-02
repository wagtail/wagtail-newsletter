import os

import pytest
import requests


def get_listmonk_credentials():
    """Get the API credentials from environment variables"""
    username = os.environ.get("WAGTAIL_NEWSLETTER_LISTMONK_USER")
    password = os.environ.get("WAGTAIL_NEWSLETTER_LISTMONK_API_KEY")

    if not username or not password:
        pytest.skip("listmonk credentials not configured")

    return username, password


def create_session():
    username, password = get_listmonk_credentials()
    auth = requests.auth.HTTPBasicAuth(username, password)
    session = requests.Session()
    session.auth = auth
    return session


def get_list_id():
    return int(os.environ.get("LISTMONK_TEST_LIST_ID", "1"))


def get_from_email():
    return os.environ.get("LISTMONK_FROM_EMAIL", "My Newsletter <hello@example.com>")


def get_server_url():
    return os.environ.get("LISTMONK_TEST_URL", "http://localhost:9000")


@pytest.fixture(scope="session", autouse=True)
def check_environment_variables():
    required_vars = [
        "LISTMONK_USER",
        "LISTMONK_API_KEY",
    ]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        pytest.skip(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
