import pytest

from django.template import Context, Template
from wagtail.models import Page, Site
from wagtail.rich_text import RichText


@pytest.mark.django_db
def test_richtext_expands_page_link():
    page = Page(title="Page")
    Site.objects.get().root_page.add_child(instance=page)

    template = Template(
        """
        {% load wagtail_newsletter %}
        {{ value|newsletter_richtext }}
        """
    )
    value = RichText(f'<a linktype="page" id="{page.pk}">link</a>')
    html = template.render(Context({"value": value}))

    assert html.strip() == '<a href="http://localhost/page/">link</a>'


@pytest.mark.django_db
def test_richtext_handles_broken_page_link():
    page = Page(title="Page")
    Site.objects.get().root_page.add_child(instance=page)

    template = Template(
        """
        {% load wagtail_newsletter %}
        {{ value|newsletter_richtext }}
        """
    )
    value = RichText('<a linktype="page" id="999999">link</a>')
    html = template.render(Context({"value": value}))

    assert html.strip() == "<a>link</a>"


@pytest.mark.django_db
def test_string_is_wrapped_as_rich_text():
    page = Page(title="Page")
    Site.objects.get().root_page.add_child(instance=page)

    template = Template(
        """
        {% load wagtail_newsletter %}
        {{ value|newsletter_richtext }}
        """
    )
    value = f'<a linktype="page" id="{page.pk}">link</a>'
    html = template.render(Context({"value": value}))

    assert html.strip() == '<a href="http://localhost/page/">link</a>'


def test_richtext_not_a_string():
    template = Template(
        """
        {% load wagtail_newsletter %}
        {{ value|newsletter_richtext }}
        """
    )
    with pytest.raises(ValueError) as error:
        template.render(Context({"value": 13}))

    assert error.match("Expected string value")
