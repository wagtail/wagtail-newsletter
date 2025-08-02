from datetime import datetime
from pathlib import Path

import pytest

from django.core.cache import caches

from wagtail_newsletter.audiences import Audience, AudienceSegment
from wagtail_newsletter.campaign_backends import CampaignBackend


@pytest.fixture(autouse=True)
def temporary_media_dir(settings, tmp_path: Path):
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture(autouse=True)
def clear_cache():
    caches["default"].clear()


class MemoryCampaignBackend(CampaignBackend):
    name = "Testing"

    def __init__(self):
        self.audiences = []
        self.segments = {}

    def validate_recipients(self, recipients) -> None:
        """Validate that the recipients meet the backend's requirements."""
        pass

    def add(self, audience: Audience, segments: "list[AudienceSegment]"):
        self.audiences.append(audience)
        self.segments[audience.id] = segments

    def get_audiences(self):
        return self.audiences

    def get_audience_segments(self, audience_id):
        if audience_id in self.segments:
            return self.segments.get(audience_id, [])
        else:
            raise Audience.DoesNotExist

    def save_campaign(self, **kwargs):
        raise NotImplementedError

    def get_campaign(self, campaign_id: str):
        raise NotImplementedError

    def send_test_email(self, *, campaign_id: str, email: str):
        raise NotImplementedError

    def send_campaign(self, campaign_id: str):
        raise NotImplementedError

    def schedule_campaign(self, campaign_id: str, schedule_time: datetime):
        raise NotImplementedError

    def unschedule_campaign(self, campaign_id: str):
        raise NotImplementedError


@pytest.fixture(autouse=True)
def memory_backend(monkeypatch: pytest.MonkeyPatch):
    backend = MemoryCampaignBackend()
    monkeypatch.setattr(
        "wagtail_newsletter.campaign_backends.get_backend",
        lambda: backend,
    )
    return backend


def pytest_addoption(parser):
    """Add custom command line options for pytest"""
    parser.addoption(
        "--enable-mail",
        action="store_true",
        default=False,
        help="Enable email sending tests",
    )


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "mail: mark tests that require email functionality"
    )
    config.addinivalue_line(
        "markers", "listmonk_integration: mark integration test (for listmonk)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip mail tests if --enable-mail is not provided"""
    if not config.getoption("--enable-mail"):
        skip_mail = pytest.mark.skip(
            reason="Email testing disabled. Use --enable-mail to enable."
        )
        for item in items:
            if "mail" in item.keywords:
                item.add_marker(skip_mail)
