from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def temporary_media_dir(settings, tmp_path: Path):
    settings.MEDIA_ROOT = tmp_path / "media"
