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
