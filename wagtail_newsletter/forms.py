from django import forms
from django.utils.timezone import get_current_timezone
from wagtail.admin.widgets import AdminDateTimeInput


class SendTestEmailForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        help_text="Send a test email to this address",
    )


class ScheduleCampaignForm(forms.Form):
    schedule_time = forms.DateTimeField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["schedule_time"].widget = AdminDateTimeInput()
        tz = get_current_timezone()
        self.fields["schedule_time"].help_text = f"Time zone is {tz}"
