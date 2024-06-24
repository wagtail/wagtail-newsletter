from datetime import datetime


project = "Wagtail Newsletter"
copyright = f"{datetime.now().year}, Torchbox and contributors. BSD license"
author = "Alex Morega"
release = "0.1.0"

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinx_wagtail_theme",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

html_theme = "sphinx_wagtail_theme"
html_static_path = ["_static"]
