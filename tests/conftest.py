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
    def __init__(self):
        self.audiences = []
        self.segments = {}

    def add(self, audience: Audience, segments: "list[AudienceSegment]"):
        self.audiences.append(audience)
        self.segments[audience.id] = segments

    def get_audiences(self):
        return self.audiences

    def get_audience_segments(self, audience_id):
        if audience_id in self.segments:
            return self.segments[audience_id]
        else:
            raise AudienceSegment.DoesNotExist


@pytest.fixture
def memory_backend(monkeypatch: pytest.MonkeyPatch):
    backend = MemoryCampaignBackend()
    monkeypatch.setattr(
        "wagtail_newsletter.campaign_backends.get_backend",
        lambda: backend,
    )
    return backend
