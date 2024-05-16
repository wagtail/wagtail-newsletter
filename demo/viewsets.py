from wagtail.admin.panels import FieldPanel

from wagtail_newsletter.viewsets import NewsletterRecipientsViewSet

from .models import CustomRecipients


class CustomRecipientsViewSet(NewsletterRecipientsViewSet):
    model = CustomRecipients
    panels = NewsletterRecipientsViewSet.panels + [
        FieldPanel("greeting"),
    ]


custom_recipients_viewset = CustomRecipientsViewSet("custom_recipients")
