from unittest.mock import Mock

import pytest

from django.urls import reverse

from wagtail_newsletter.viewsets import Audience, AudienceSegment

from .conftest import MemoryCampaignBackend


@pytest.fixture(autouse=True)
def backend(memory_backend: MemoryCampaignBackend):
    memory_backend.add(
        Audience(id="be13e6ca91", name="Torchbox", member_count=8),
        [
            AudienceSegment(
                id="be13e6ca91/2103836", name="Segment One", member_count=3
            ),
            AudienceSegment(
                id="be13e6ca91/2103837", name="Segment Two", member_count=1
            ),
            AudienceSegment(
                id="be13e6ca91/2103838", name="Segment Three", member_count=1
            ),
        ],
    )

    memory_backend.add(Audience(id="9af08f2afa", name="Other", member_count=13), [])
    return memory_backend


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
    backend.get_audiences = Mock(side_effect=backend.get_audiences)
    a1 = Audience.objects.get(pk="be13e6ca91")
    a2 = Audience.objects.get(pk="be13e6ca91")
    assert (a1.id, a1.name, a1.member_count) == (a2.id, a2.name, a2.member_count)
    assert backend.get_audiences.call_count == 1


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
    backend.get_audience_segments = Mock(side_effect=backend.get_audience_segments)
    s1 = AudienceSegment.objects.get(pk="be13e6ca91/2103836")
    s2 = AudienceSegment.objects.get(pk="be13e6ca91/2103836")
    assert (s1.id, s1.name, s1.member_count) == (s2.id, s2.name, s2.member_count)
    assert backend.get_audience_segments.call_count == 1


def test_audience_segment_get_deleted():
    with pytest.raises(AudienceSegment.DoesNotExist):
        AudienceSegment.objects.get(pk="be13e6ca91/deleted_segment")


def test_audience_segment_get_audience_deleted():
    assert list(AudienceSegment.objects.filter(audience="no-such-audience")) == []


def test_audience_segment_with_no_audience():
    assert list(AudienceSegment.objects.all()) == []


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
