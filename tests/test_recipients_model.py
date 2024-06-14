import pytest

from django.core.exceptions import ValidationError

from wagtail_newsletter.audiences import Audience, AudienceSegment
from wagtail_newsletter.models import NewsletterRecipients
from wagtail_newsletter.test.models import ArticlePage, CustomRecipients

from .conftest import MemoryCampaignBackend


def test_custom_recipients_model_foreign_key():
    fields = {field.name: field for field in ArticlePage._meta.fields}
    assert fields["newsletter_recipients"].related_model is CustomRecipients


@pytest.mark.parametrize(
    "audience,segment,expected",
    [
        (None, None, None),  # no audience or segment
        ("audience1", None, 10),  # existing audience
        ("audience2", None, None),  # audience not found
        ("audience1", "audience1/segment1", 5),  # existing segment
        ("audience1", "audience1/segment2", None),  # segment not found
    ],
)
def test_recipients_member_count(
    audience, segment, expected, memory_backend: MemoryCampaignBackend
):
    memory_backend.add(
        Audience(id="audience1", member_count=10),
        [AudienceSegment(id="audience1/segment1", member_count=5)],
    )

    recipients = NewsletterRecipients(audience=audience, segment=segment)
    assert recipients.member_count == expected


@pytest.mark.parametrize(
    "audience,segment,is_valid",
    [
        ("audience1", None, True),
        ("audience1", "audience1/segment1", True),
        ("audience1", "audience1/segment2", False),
        ("audience1", "audience2/segment1", False),
    ],
)
def test_segment_validation(
    audience, segment, is_valid, memory_backend: MemoryCampaignBackend
):
    memory_backend.add(
        Audience(id="audience1", member_count=10),
        [AudienceSegment(id="audience1/segment1", member_count=5)],
    )

    recipients = NewsletterRecipients(name="test", audience=audience, segment=segment)

    if is_valid:
        # should raise no exception
        recipients.full_clean()

    else:
        with pytest.raises(ValidationError) as error:
            recipients.full_clean()

        assert error.match(r"The segment is not part of the selected audience.")


def test_str():
    NAME = "test"
    recipients = NewsletterRecipients(name=NAME)
    assert str(recipients) == NAME
