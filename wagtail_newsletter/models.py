from typing import Any, Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.models import Page
from wagtail.permissions import ModelPermissionPolicy

from . import audiences, get_recipients_model_string, panels


class NewsletterRecipientsBase(models.Model):
    name = models.CharField(max_length=1000)
    audience = models.CharField(max_length=1000)
    segment = models.CharField(max_length=1000, blank=True, null=True)  # noqa: DJ001

    class Meta:  # type: ignore
        abstract = True

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()

        if self.segment:
            # If this were a normal queryset, we could have called `.exists()`, but
            # queryish doesn't support `.exists()`, and in any case, it has to perform
            # a `list_segments` API call.
            segment_ids = [
                segment.id
                for segment in audiences.AudienceSegment.objects.filter(
                    audience=self.audience
                )
            ]
            if self.segment not in segment_ids:
                raise ValidationError(
                    {"segment": "The segment is not part of the selected audience."}
                )

    @property
    def member_count(self) -> Optional[int]:
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
    # Campaign ID in the backend system. We store it as an opaque string.
    newsletter_campaign = models.CharField(max_length=1000, blank=True)

    class Meta:  # type: ignore
        abstract = True

    @classmethod
    def get_newsletter_panels(cls):
        from .viewsets import recipients_chooser_viewset

        return [
            FieldPanel(
                "newsletter_recipients",
                heading="Recipients",
                widget=recipients_chooser_viewset.widget_class,
            ),
            FieldPanel("newsletter_subject", heading="Subject"),
            panels.NewsletterPanel(heading="Campaign"),
        ]

    preview_modes = [  # type: ignore
        ("", _("Default")),
        ("newsletter", _("Newsletter")),
    ]

    @classmethod
    def get_edit_handler(cls):  # pragma: no cover
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

    def has_newsletter_permission(self, user, action):
        permission_policy = ModelPermissionPolicy(type(self))
        return permission_policy.user_has_permission(user, "publish")

    newsletter_template: str

    def get_newsletter_template(self) -> str:
        return self.newsletter_template

    def get_newsletter_context(self) -> "dict[str, Any]":
        return {"page": self}

    def get_newsletter_html(self) -> SafeString:
        return render_to_string(
            template_name=self.get_newsletter_template(),
            context=self.get_newsletter_context(),
        )

    def serve_preview(self, request, mode_name):  # type: ignore
        if mode_name == "newsletter":
            return HttpResponse(self.get_newsletter_html().encode())

        return super().serve_preview(request, mode_name)
