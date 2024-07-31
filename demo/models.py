from datetime import date

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.permission_policies.base import ModelPermissionPolicy

from wagtail_newsletter.models import NewsletterPageMixin, NewsletterRecipientsBase

from .blocks import StoryBlock
from .fields import StreamField


class ArticlePage(NewsletterPageMixin, Page):  # type: ignore
    author = models.CharField(max_length=255, blank=True)
    date = models.DateField("Publishing date", default=date.today)
    body = StreamField(StoryBlock(), blank=True, use_json_field=True)

    newsletter_preview = models.CharField(
        max_length=1000,
        blank=True,
        help_text="The preview that will be displayed in the inbox of the recipient.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("author"),
        FieldPanel("date"),
        FieldPanel("body"),
    ]

    newsletter_template = "demo/article_page_newsletter.html"

    class Meta:  # type: ignore
        permissions = [
            ("sendnewsletter_articlepage", "Can send newsletter"),
        ]

    def has_newsletter_permission(self, user, action):
        permission_policy = ModelPermissionPolicy(type(self))
        return permission_policy.user_has_permission(user, "sendnewsletter")

    @classmethod
    def get_newsletter_panels(cls):
        panels = [panel.clone() for panel in super().get_newsletter_panels()]
        panels.insert(-1, FieldPanel("newsletter_preview", heading="Preview"))
        for panel in panels:
            panel.permission = "demo.sendnewsletter_articlepage"
        return panels

    def get_newsletter_context(self):
        context = super().get_newsletter_context()
        context["rendering_newsletter"] = True
        return context


class CustomRecipients(NewsletterRecipientsBase):
    greeting = RichTextField(blank=True)

    class Meta:  # type: ignore
        verbose_name_plural = "Custom recipients"
