from django.apps import apps
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from . import get_recipients_model_string
from .models import NewsletterRecipientsBase


def recipients(request):
    model = apps.get_model(get_recipients_model_string())
    recipients: NewsletterRecipientsBase = get_object_or_404(
        model,  # type: ignore
        pk=request.GET.get("pk"),
    )

    return JsonResponse(
        {
            "name": recipients.name,
            "member_count": recipients.member_count,
        }
    )
