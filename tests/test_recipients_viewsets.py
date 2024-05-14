from unittest.mock import Mock

import pytest

from django.core.cache import caches
from django.urls import reverse

from wagtail_newsletter.campaign_backends.mailchimp import MailchimpCampaignBackend
from wagtail_newsletter.viewsets import Audience, AudienceSegment


class MockMailchimpCampaignBackend(MailchimpCampaignBackend):
    def __init__(self):
        self.client = Mock()


@pytest.fixture(autouse=True)
def memory_cache(settings):
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }
    caches["default"].clear()


@pytest.fixture(autouse=True)
def backend(monkeypatch: pytest.MonkeyPatch):
    backend = MockMailchimpCampaignBackend()

    backend.client.lists.get_all_lists.return_value = {
        "lists": [
            {"id": "be13e6ca91", "name": "Torchbox", "stats": {"member_count": 8}},
            {"id": "9af08f2afa", "name": "Other", "stats": {"member_count": 13}},
        ],
    }

    backend.client.lists.list_segments.return_value = {
        "list_id": "be13e6ca91",
        "segments": [
            {"id": 2103836, "member_count": 3, "name": "Segment One"},
            {"id": 2103837, "member_count": 1, "name": "Segment Two"},
            {"id": 2103838, "member_count": 1, "name": "Segment Three"},
        ],
    }

    monkeypatch.setattr(
        "wagtail_newsletter.campaign_backends.get_backend",
        lambda: backend,
    )
    return backend


def test_audience_chooser(admin_client):
    response = admin_client.get(reverse("audience_chooser:choose"))
    results = response.context["results"]
    assert [obj.pk for obj in results.object_list] == ["be13e6ca91", "9af08f2afa"]


def test_audience_get_instance():
    audience = Audience.objects.get(pk="be13e6ca91")
    assert audience.pk == "be13e6ca91"
    assert audience.name == "Torchbox"
    assert audience.member_count == 8


def test_audience_get_instance_is_cached(backend):
    a1 = Audience.objects.get(pk="be13e6ca91")
    a2 = Audience.objects.get(pk="be13e6ca91")
    assert (a1.id, a1.name, a1.member_count) == (a2.id, a2.name, a2.member_count)
    assert backend.client.lists.get_all_lists.call_count == 1


def test_audience_get_deleted():
    with pytest.raises(Audience.DoesNotExist):
        Audience.objects.get(pk="deleted_audience")


def test_audience_segment_chooser(admin_client):
    url = f"{reverse('audience_segment_chooser:choose')}?audience=be13e6ca91"
    response = admin_client.get(url)
    results = response.context["results"]
    assert [obj.pk for obj in results.object_list] == [
        "be13e6ca91/2103836",
        "be13e6ca91/2103837",
        "be13e6ca91/2103838",
    ]


def test_audience_segment_get_instance():
    segment = AudienceSegment.objects.get(pk="be13e6ca91/2103836")
    assert segment.pk == "be13e6ca91/2103836"
    assert segment.name == "Segment One"
    assert segment.member_count == 3


def test_audience_segment_get_instance_is_cached(backend):
    s1 = AudienceSegment.objects.get(pk="be13e6ca91/2103836")
    s2 = AudienceSegment.objects.get(pk="be13e6ca91/2103836")
    assert (s1.id, s1.name, s1.member_count) == (s2.id, s2.name, s2.member_count)
    assert backend.client.lists.list_segments.call_count == 1


def test_audience_segment_get_deleted():
    with pytest.raises(AudienceSegment.DoesNotExist):
        AudienceSegment.objects.get(pk="be13e6ca91/deleted_segment")


def test_non_admin_user_access_denied(client):
    audience_response = client.get(reverse("audience_chooser:choose"))
    assert audience_response.status_code == 302
    assert audience_response.url.startswith(reverse("wagtailadmin_login"))

    url = f"{reverse('audience_segment_chooser:choose')}?audience=be13e6ca91"
    segment_response = client.get(url)
    assert segment_response.status_code == 302
    assert segment_response.url.startswith(reverse("wagtailadmin_login"))


def test_queryish_extra_filters_raises_exception():
    with pytest.raises(RuntimeError) as error:
        Audience.objects.filter(foo="bar").first()

    assert str(error.value) == "Filters not supported: {'foo': 'bar'}"


def test_audience_segment_with_no_audience_raises_exception():
    with pytest.raises(RuntimeError) as error:
        AudienceSegment.objects.first()

    assert str(error.value) == "Cannot determine audience ID"
