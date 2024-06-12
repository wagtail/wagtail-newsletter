import pytest

from django.template import Context, Template, TemplateSyntaxError
from django.utils.safestring import mark_safe

from wagtail_newsletter.templatetags.wagtail_newsletter import MRMLError


def test_render_mjml():
    template = Template(
        """
        {% load wagtail_newsletter %}
        {% mrml %}
            <mjml>
                <mj-body>
                    {{ message }}
                </mj-body>
            </mjml>
        {% endmrml %}
        """
    )
    message = "<em>Hello MJML!</em>"
    html = template.render(Context({"message": mark_safe(message)}))  # noqa: S308
    assert message in html
    # Since this was rendered for email, it should have some weird markup inside.
    assert "<o:OfficeDocumentSettings>" in html


def test_mrml_tag_receives_no_arguments():
    with pytest.raises(TemplateSyntaxError) as error:
        Template(
            """
            {% load wagtail_newsletter %}
            {% mrml unexpected_argument %}{% endmrml %}
            """
        )

    assert error.match("'mrml' tag doesn't receive any arguments.")


def test_render_mjml_syntax_error():
    template = Template(
        """
        {% load wagtail_newsletter %}
        {% mrml %}
            <mjml>
            no closing tag
        {% endmrml %}
        """
    )
    with pytest.raises(MRMLError) as error:
        template.render(Context())

    assert error.match("Failed to render MJML: 'unexpected token")
