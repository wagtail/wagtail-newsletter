from django import forms


class SendTestEmailForm(forms.Form):
    newsletter_test_email_address = forms.EmailField()
