from django.apps import apps
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from wagtail.admin.auth import permission_denied
from wagtail.admin.views.pages.history import PageHistoryReportFilterSet
from wagtail.admin.views.reports import ReportView
from wagtail.models import Page
from wagtail.models.audit_log import log_action_registry

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


def get_actions_for_filter():
    # Only return those actions used by newsletter log entries.
    actions = set(NewsletterLogEntry.objects.all().get_actions())  # type: ignore
    return [
        action for action in log_action_registry.get_choices() if action[0] in actions
    ]


class NewsletterHistoryReportFilterSet(PageHistoryReportFilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["action"].extra["choices"] = get_actions_for_filter()


class NewsletterHistoryView(ReportView):
    template_name = "wagtailadmin/pages/history.html"
    title = "Newsletter history"
    header_icon = "history"
    paginate_by = 20
    filterset_class = NewsletterHistoryReportFilterSet

    def dispatch(self, request, *args, **kwargs):
        page = get_object_or_404(Page, id=kwargs.pop("page_id")).specific

        if not isinstance(page, NewsletterPageMixin):
            raise Http404

        if not page.has_newsletter_permission(request.user, "save_campaign"):
            return permission_denied(request)

        self.page = page

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context["page"] = self.page
        context["subtitle"] = self.page.get_admin_display_title()
        context["page_latest_revision"] = self.page.get_latest_revision()

        return context

    def get_queryset(self):
        return NewsletterLogEntry.objects.filter(page=self.page).select_related(
            "revision", "user", "user__wagtail_userprofile"
        )
