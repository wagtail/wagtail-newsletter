from datetime import datetime
from email.utils import parseaddr

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _require_setting(name):
    value = getattr(settings, name, None)
    if value is None:
        raise ImproperlyConfigured(f"{name} is not set")
    return value


def valid_email(s: str):
    p = parseaddr(s)
    if "@" not in p[1]:
        return False
    return True


def valid_time(s: str):
    try:
        datetime.fromisoformat(s)
    except Exception:
        return False
    return True
