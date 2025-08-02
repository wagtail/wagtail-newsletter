import json

from typing import Optional

import requests


class APIClientError(Exception):
    def __init__(self, text: str, status_code: Optional[int] = None):
        try:
            t = json.loads(text)
            self.text = t.get("message", "")
        except json.JSONDecodeError:
            self.text = ""
        self.status_code = status_code

    def __str__(self):
        parts = [f"{self.__class__.__name__}:"]
        if self.status_code is not None:
            parts.append(f"Status Code: {self.status_code}")
        parts.append(f"Message: {self.text}")
        return " ".join(parts)


def _handle_response(response: requests.Response) -> dict:
    """
    Handles the response from the API, checking for errors and parsing JSON.
    """
    content_type = response.headers.get("Content-Type", "")
    if "application/json" not in content_type:
        raise APIClientError(text=response.text, status_code=response.status_code)

    try:
        data = response.json()
    except ValueError as e:
        raise APIClientError(
            f"Invalid JSON response: {e}",
            status_code=response.status_code,
            text=response.text,
        ) from e

    if not response.ok:
        raise APIClientError(text=response.text, status_code=response.status_code)

    return data
