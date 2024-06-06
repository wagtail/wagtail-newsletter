from wagtail.admin.panels import Panel


class NewsletterPanel(Panel):
    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtail_newsletter/panels/newsletter_panel.html"
