from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.models import Page

from . import audiences, get_recipients_model_string


class NewsletterRecipientsBase(models.Model):
    name = models.CharField(max_length=1000)
    audience = models.CharField(max_length=1000)
    segment = models.CharField(max_length=1000, blank=True, null=True)  # noqa: DJ001

    class Meta:  # type: ignore
        abstract = True

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        if self.segment:
            try:
                return audiences.AudienceSegment.objects.get(
                    pk=self.segment
                ).member_count
            except audiences.AudienceSegment.DoesNotExist:
                return None

        elif self.audience:
            try:
                return audiences.Audience.objects.get(pk=self.audience).member_count
            except audiences.Audience.DoesNotExist:
                return None

        else:
            return None


class NewsletterRecipients(NewsletterRecipientsBase):
    class Meta:  # type: ignore
        verbose_name_plural = "Newsletter recipients"


class NewsletterPageMixin(Page):
    base_form_class: type

    newsletter_recipients = models.ForeignKey(
        get_recipients_model_string(),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    newsletter_subject = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Subject for the newsletter. Defaults to page title if blank.",
    )
    newsletter_campaign = models.CharField(max_length=1000, blank=True)

    class Meta:  # type: ignore
        abstract = True

    @classmethod
    def get_newsletter_panels(cls):
        from .viewsets import recipients_chooser_viewset

        return [
            FieldPanel(
                "newsletter_recipients",
                widget=recipients_chooser_viewset.widget_class,
            ),
            FieldPanel("newsletter_subject"),
        ]

    @classmethod
    def get_edit_handler(cls):
        tabs = []

        if cls.content_panels:
            tabs.append(ObjectList(cls.content_panels, heading=_("Content")))
        if cls.promote_panels:
            tabs.append(ObjectList(cls.promote_panels, heading=_("Promote")))
        if cls.settings_panels:
            tabs.append(ObjectList(cls.settings_panels, heading=_("Settings")))

        tabs.append(ObjectList(cls.get_newsletter_panels(), heading=_("Newsletter")))

        edit_handler = TabbedInterface(tabs, base_form_class=cls.base_form_class)

        return edit_handler.bind_to_model(cls)

    # Fields which are always saved on the page model and overwritten when loading
    # revisions. In effect, these fields behave as if they were not versioned.
    # Subclasses may add their own newsletter-related fields to this list.
    newsletter_persistent_fields = [
        "newsletter_recipients",
        "newsletter_subject",
        "newsletter_campaign",
    ]

    def with_content_json(self, content):
        obj = super().with_content_json(content)
        for field in self.newsletter_persistent_fields:
            setattr(obj, field, getattr(self, field))
        return obj

    def save_revision(self, *args, **kwargs):
        revision = super().save_revision(*args, **kwargs)
        self.save(
            update_fields=self.newsletter_persistent_fields,
            clean=False,
        )
        return revision
