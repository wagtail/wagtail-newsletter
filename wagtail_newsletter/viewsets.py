from wagtail.admin.panels import FieldPanel
from wagtail.admin.ui.tables import Column
from wagtail.admin.views.generic.chooser import ChooseView
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.admin.viewsets.model import ModelViewSet

from . import get_recipients_model_string
from .audiences import Audience, AudienceSegment
from .models import NewsletterRecipients


class AudienceChooseView(ChooseView):
    @property
    def columns(self):  # type: ignore
        return super().columns + [
            Column("member_count", label="Members", accessor="member_count"),
        ]


class AudienceChooserViewSet(ChooserViewSet):
    model = Audience
    icon = "group"
    choose_one_text = "Choose an audience"
    choose_another_text = "Choose another audience"
    choose_view_class = AudienceChooseView


audience_chooser_viewset = AudienceChooserViewSet("audience_chooser")


class AudienceSegmentChooserViewSet(ChooserViewSet):
    model = AudienceSegment
    icon = "group"
    choose_one_text = "Choose an audience segment"
    choose_another_text = "Choose another audience segment"
    url_filter_parameters = ["audience"]
    preserve_url_parameters = ["multiple", "audience"]
    choose_view_class = AudienceChooseView


audience_segment_chooser_viewset = AudienceSegmentChooserViewSet(
    "audience_segment_chooser"
)


class NewsletterRecipientsViewSet(ModelViewSet):
    model = NewsletterRecipients
    icon = "group"
    add_to_settings_menu = True

    form_fields = [
        "name",
        "audience",
        "segment",
    ]

    panels = [
        FieldPanel("name"),
        FieldPanel("audience", widget=audience_chooser_viewset.widget_class),
        FieldPanel(
            "segment",
            widget=audience_segment_chooser_viewset.widget_class(  # type: ignore
                linked_fields={"audience": "#id_audience"},
            ),
        ),
    ]


newsletter_recipients_viewset = NewsletterRecipientsViewSet("newsletter_recipients")


class RecipientsChooserViewSet(ChooserViewSet):
    model = get_recipients_model_string()
    icon = "group"
    choose_one_text = "Choose recipients"
    choose_another_text = "Choose other recipients"
    choose_view_class = AudienceChooseView


recipients_chooser_viewset = RecipientsChooserViewSet("recipients_chooser")
