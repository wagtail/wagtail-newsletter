from datetime import datetime


project = "Wagtail Newsletter"
copyright = f"{datetime.now().year}, Torchbox and contributors. BSD license"
author = "Alex Morega"
release = "0.1.0"

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx_wagtail_theme",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

html_theme = "sphinx_wagtail_theme"
html_theme_options = {
    "project_name": "Wagtail Newsletter documentation",
    "github_url": "https://github.com/wagtail/wagtail-newsletter/blob/main/docs/",
}

html_static_path = ["_static"]

intersphinx_mapping = {
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        "https://docs.djangoproject.com/en/stable/_objects/",
    ),
}
intersphinx_disabled_reftypes = ["*"]
