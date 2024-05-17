from django import template
from django.utils.safestring import mark_safe
from wagtail.rich_text import RichText

from ..rich_text import rewrite_db_html_for_email


register = template.Library()


@register.filter
def newsletter_richtext(value):
    if not isinstance(value, RichText):
        if not isinstance(value, str):
            raise ValueError("Expected string value")
        value = RichText(value)

    return mark_safe(rewrite_db_html_for_email(value))  # noqa: S308


class MRMLError(Exception):
    pass


class MRMLRenderNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context) -> str:
        # Importing here because mrml is an optional dependency
        import mrml

        mjml_source = self.nodelist.render(context)
        try:
            return mrml.to_html(mjml_source)
        except OSError as error:
            # The MRML library raises OSError exceptions when something goes wrong.
            message = error.args[0]
            raise MRMLError(f"Failed to render MJML: {message!r}") from error


@register.tag(name="mrml")
def mrml_tag(parser, token) -> MRMLRenderNode:
    """
    Compile MJML template after rendering the contents as a django template.

    Usage:
        {% mrml %}
            .. MJML template code ..
        {% endmrml %}
    """
    nodelist = parser.parse(("endmrml",))
    parser.delete_first_token()
    tokens = token.split_contents()
    if len(tokens) != 1:
        raise template.TemplateSyntaxError(
            f"{tokens[0]!r} tag doesn't receive any arguments."
        )
    return MRMLRenderNode(nodelist)
