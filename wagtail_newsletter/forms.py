from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import get_current_timezone, now
from wagtail.admin.widgets import AdminDateTimeInput


class SendTestEmailForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        help_text="Send a test email to this address",
    )


def require_future_date(value):
    if value <= now():
        raise ValidationError("Date must be in the future.")


class ScheduleCampaignForm(forms.Form):
    schedule_time = forms.DateTimeField(validators=[require_future_date])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["schedule_time"].widget = AdminDateTimeInput()
        tz = get_current_timezone()
        self.fields["schedule_time"].help_text = f"Time zone is {tz}"
