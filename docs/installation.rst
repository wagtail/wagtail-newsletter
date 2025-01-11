Installation
============

Here are the steps to install and configure ``wagtail-newsletter`` for your
site. They assume that you'll be sending campaigns through Mailchimp_ using the
default campaign backend.

.. _Mailchimp: https://mailchimp.com

Install the package from PyPI
-----------------------------

.. code-block:: shell

  pip install 'wagtail-newsletter[mailchimp,mrml]'

Configure Django settings
-------------------------

Add the app to ``INSTALLED_APPS``:

.. code-block:: python

  INSTALLED_APPS = [
      # ...
      "wagtail_newsletter",
  ]

For ``WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY``, `get an API key`_ from Mailchimp.

The ``WAGTAIL_NEWSLETTER_FROM_NAME`` and ``WAGTAIL_NEWSLETTER_REPLY_TO``
settings are used to build the `From:` field in the outgoing emails:

.. _get an API key: https://us1.admin.mailchimp.com/account/api/

.. code-block:: python

  WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY = "the-mailchimp-api-key"
  WAGTAIL_NEWSLETTER_FROM_NAME = "Example Newsletter"
  WAGTAIL_NEWSLETTER_REPLY_TO = "newsletter@example.com"

Set up a page model for newsletters
-----------------------------------

Add ``NewsletterPageMixin`` to a page model:

.. code-block:: python

  from wagtail.admin.panels import FieldPanel
  from wagtail.fields import RichTextField
  from wagtail.models import Page
  from wagtail_newsletter.models import NewsletterPageMixin

  class ArticlePage(NewsletterPageMixin, Page):
      body = RichTextField()

      content_panels = Page.content_panels + [
          FieldPanel("body"),
      ]

      # replace app_name with your app name
      newsletter_template = "app_name/article_page_newsletter.html"

.. note::

  ``NewsletterPageMixin`` adds extra model fields to the page model, so you
  need to run ``django-admin makemigrations`` and ``django-admin migrate`` to
  add them to the database.

Create a page template for the email body
(``templates/demo/article_page_newsletter.html``). The content of the template
is completely up to you, but writing email-compatible HTML is notoriously
difficult, so *wagtail-newsletter* includes a template tag ``{% mrml %}``, that
transforms its contents from MJML_ into email-compatible HTML. Behind the
scenes it uses the mrml_ library.

.. _MJML: https://mjml.io
.. _mrml: https://github.com/jdrouet/mrml

.. code-block:: htmldjango

  {% load wagtail_newsletter %}

  {% mrml %}
      <mjml>
          <mj-body>
              <h1>{{ page.title }}</h1>
              {{ page.body|newsletter_richtext }}
          </mj-body>
      </mjml>
  {% endmrml %}

Configure recipients
--------------------

Finally, we need to configure recipients for our newsletteres. Go to Wagtail
admin and click on *Settings*, then *Newsletter Recipients*, and create a new
Recipients record. Give it a descriptive name, and select an *audience* from
Mailchimp, and optionally an *audience segment*, and click *Create*. When
preparing a newsletter page, you can select this *Recipients* record to use as
recipients for the campaign.

Configure a Django cache
------------------------

In Wagtail Admin, when displaying recipients, an audience, or an audience
segment, wagtail-newsletter must perform API calls to retrieve information like
the audience name and number of subscribers. To avoid repeated API calls it's
useful to set up Django's cache_ mechanism. Wagtail-newsletter will use the
`default` cache, and store information for 5 minutes (configurable via the
``WAGTAIL_NEWSLETTER_CACHE_TIMEOUT`` setting).

.. _cache: https://docs.djangoproject.com/en/stable/topics/cache/#setting-up-the-cache

Next steps
----------

That's it! Now, when editing an ``ArticlePage`` in Wagtail Admin, you can `flip
the preview mode`_ to *Newsletter*, and see the article in email format. When
you're happy with the results, go to the *Newsletter* tab in the editor to
:ref:`send a test email <Send test email>` and then :ref:`send your campaign
<Send campaign>`.

.. _flip the preview mode: https://docs.wagtail.org/en/stable/reference/pages/model_reference.html#wagtail.models.Page.preview_modes
