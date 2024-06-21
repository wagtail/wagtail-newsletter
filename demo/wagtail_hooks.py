from django.contrib.auth.models import Permission
from wagtail import hooks

from . import viewsets


@hooks.register("register_admin_viewset")  # type: ignore
def register_admin_viewset():
    return viewsets.custom_recipients_viewset


@hooks.register("register_permissions")  # type: ignore
def register_permissions():  # pragma: no cover
    return Permission.objects.filter(
        content_type__app_label="demo",
        codename__in=[
            "add_customrecipients",
            "change_customrecipients",
            "delete_customrecipients",
            "sendnewsletter_articlepage",
        ],
    )
