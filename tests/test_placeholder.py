"""
Placeholder test, so that pytest doesn't fail with an empty testsuite. Feel free to
remove this when you start writing tests.
https://github.com/pytest-dev/pytest/issues/2393
"""

import pytest


pytestmark = pytest.mark.django_db


def test_homepage(client):
    assert client.get("/").status_code == 200
