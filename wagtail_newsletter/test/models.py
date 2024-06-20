from wagtail.fields import RichTextField
from wagtail.models import Page

from wagtail_newsletter.models import NewsletterPageMixin, NewsletterRecipientsBase


class CustomRecipients(NewsletterRecipientsBase):
    greeting = RichTextField(blank=True)

    class Meta:  # type: ignore
        verbose_name_plural = "Custom recipients"


class ArticlePage(NewsletterPageMixin, Page):  # type: ignore
    body = RichTextField(blank=True)

    newsletter_template = "wagtail_newsletter_test/newsletter.html"


class SimplePage(Page):
    body = RichTextField(blank=True)
