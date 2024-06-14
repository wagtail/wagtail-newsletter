from django import forms


class SendTestEmailForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        help_text="Send a test email to this address",
    )
