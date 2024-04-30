from wagtail import hooks

from . import viewsets


@hooks.register("register_admin_viewset")  # type: ignore
def register_admin_viewset():
    return viewsets.custom_recipients_viewset
