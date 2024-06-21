from django.apps import apps
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from wagtail.admin.auth import permission_denied
from wagtail.admin.views.generic.history import HistoryView
from wagtail.models import Page

from . import get_recipients_model_string
from .models import NewsletterLogEntry, NewsletterPageMixin, NewsletterRecipientsBase


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


class NewsletterHistoryView(HistoryView):
    object: NewsletterPageMixin

    def get_object(self):
        page = get_object_or_404(Page, id=self.pk).specific

        if not isinstance(page, NewsletterPageMixin):
            raise Http404

        return page

    def dispatch(self, request, *args, **kwargs):
        if not self.object.has_newsletter_permission(
            self.request.user, "save_campaign"
        ):
            return permission_denied(self.request)

        return super().dispatch(request, *args, **kwargs)

    # XXX Wagtail 5.2 expects a `model` property to generate the message
    # "Edit this {model_name}", which is not displayed in our case
    @property
    def model(self):  # pragma: no cover
        return type(self.object)

    # XXX Wagtail 5.2 doesn't have the `_annotate_queryset` method
    def _annotate_queryset(self, queryset):  # pragma: no cover
        if hasattr(self, "_annotate_queryset"):
            return super()._annotate_queryset(queryset)

        return queryset.select_related("revision", "user", "user__wagtail_userprofile")

    # XXX Wagtail 6.0 calls `get_queryset` directly
    def get_queryset(self):
        return NewsletterLogEntry.objects.for_instance(self.object)  # type: ignore

    # XXX Wagtail 6.1 can't deal with a Null `permission_policy` so we stub out
    # `user_can_unschedule`
    def user_can_unschedule(self):
        return False

    def get_base_queryset(self):
        return self._annotate_queryset(self.get_queryset())
