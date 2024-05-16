from datetime import date

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from wagtail_newsletter.models import NewsletterPageMixin, NewsletterRecipientsBase

from .blocks import StoryBlock
from .fields import StreamField


class ArticlePage(NewsletterPageMixin, Page):  # type: ignore
    author = models.CharField(max_length=255, blank=True)
    date = models.DateField("Publishing date", default=date.today)
    body = StreamField(StoryBlock(), blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("author"),
        FieldPanel("date"),
        FieldPanel("body"),
    ]


class CustomRecipients(NewsletterRecipientsBase):
    greeting = RichTextField(blank=True)

    class Meta:  # type: ignore
        verbose_name_plural = "Custom recipients"
