from copy import copy
from functools import lru_cache

from django.utils.html import escape
from wagtail.models import Page
from wagtail.rich_text import EmbedRewriter, LinkRewriter, MultiRuleRewriter, features
from wagtail.rich_text.pages import PageLinkHandler


def rewrite_db_html_for_email(rich_text):
    rewriter = _get_rewriter_for_email()
    return rewriter(rich_text.source)


class LinkHandlerForEmail(PageLinkHandler):
    @classmethod
    def expand_db_attributes(cls, attrs):
        try:
            page = cls.get_instance(attrs)
            full_url = page.localized.specific.full_url  # type: ignore
            return f'<a href="{escape(full_url)}">'
        except Page.DoesNotExist:
            return "<a>"


@lru_cache(maxsize=None)
def _get_rewriter_for_email():
    embed_rules = copy(features.get_embed_types())
    link_rules = copy(features.get_link_types())
    link_rules["page"] = LinkHandlerForEmail
    return MultiRuleRewriter(
        [
            LinkRewriter(
                {
                    linktype: handler.expand_db_attributes
                    for linktype, handler in link_rules.items()
                },
            ),
            EmbedRewriter(
                {
                    embedtype: handler.expand_db_attributes
                    for embedtype, handler in embed_rules.items()
                },
            ),
        ]
    )
