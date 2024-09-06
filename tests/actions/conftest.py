import pytest

from wagtail.models import Site

from wagtail_newsletter.test.models import ArticlePage


@pytest.fixture
def page():
    page = ArticlePage(title="Test Article")
    Site.objects.get().root_page.add_child(instance=page)
    return page
