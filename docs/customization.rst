Customization
=============

Newsletter templates
--------------------

Wagtail-newsletter will look for an attribute named ``newsletter_template`` (or
a method named ``get_newsletter_template``) to get the name of the page
template to use for newsletters. Typically this will be a dedicated template
that produces email-compatible HTML.

The ``{% mrml %}`` template tag
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To help generate email-compatible HTML, wagtail-newsletter provides a template
tag that expects MJML_ markup, and runs mrml_ behind the scenes, to transform
it into HTML.

.. code-block:: htmldjango

  {% load wagtail_newsletter %}

  {% mrml %}
      <mjml>
          <mj-body>
              <h1>{{ page.title }}</h1>
          </mj-body>
      </mjml>
  {% endmrml %}

.. _MJML: https://mjml.io
.. _mrml: https://github.com/jdrouet/mrml

The ``newsletter_richtext`` filter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Wagtail provides a `richtext template filter`_ that expands references to
embedded images and links. It generates path-only URLs, like
``/media/images/bird.jpg`` and ``/about/contact``. In the context of a web
page, they work, because the browser knows to use the domain of the current
page. In the context of emails, the domain is unknown, so those links will
break.

To address this issue, wagtail-newsletter provides a ``newsletter_richtext``
filter, that does the same thing as ``richtext``, but generates full URLs like
``https://example.com/media/images/bird.jpg`` and
``https://example.com/about/contact``.

.. _richtext template filter: https://docs.wagtail.org/en/stable/topics/writing_templates.html#rich-text-filter

.. code-block:: htmldjango

  {% load wagtail_newsletter %}

  {{ page.body|newsletter_richtext }}

Recipients model
----------------

The default recipients model in wagtail-newsletter is intentionally simple: it
has a name and a reference to an audience (and, optionally, a segment) in the
campaign provider's system. If you want to associate more information with a
recipients record, like a custom greeting or footer text, you can define a
custom model:

.. code-block:: python

  from wagtail.fields import RichTextField
  from wagtail_newsletter.models import NewsletterRecipientsBase

  class CustomRecipients(NewsletterRecipientsBase):
      greeting = RichTextField(blank=True)

      class Meta:
          verbose_name_plural = "Custom recipients"

Configure wagtail-newsletter to use the custom model by adding a setting to
Django settings:

.. code-block:: python

  WAGTAIL_NEWSLETTER_RECIPIENTS_MODEL = "myapp.CustomRecipients"

Register a viewset, and permissions, for the custom recipients model:

.. code-block:: python

  from django.contrib.auth.models import Permission
  from wagtail import hooks
  from wagtail.admin.panels import FieldPanel
  from wagtail_newsletter.viewsets import NewsletterRecipientsViewSet
  from .models import CustomRecipients

  class CustomRecipientsViewSet(NewsletterRecipientsViewSet):
      model = CustomRecipients
      panels = NewsletterRecipientsViewSet.panels + [
          FieldPanel("greeting"),
      ]

  @hooks.register("register_admin_viewset")
  def register_admin_viewset():
      return CustomRecipientsViewSet("custom_recipients")

  @hooks.register("register_permissions")
  def register_permissions():
      return Permission.objects.filter(
          content_type__app_label="myapp",
          codename__in=[
              "add_customrecipients",
              "change_customrecipients",
              "delete_customrecipients",
          ],
      )

Finally, use content from the custom recipients model in the newsletter template:

.. code-block:: htmldjango

  {% load wagtail_newsletter %}

  {% mrml %}
      <mjml>
          <mj-body>
              <h1>{{ page.title }}</h1>

              {% if page.newsletter_recipients.greeting %}
                    {{ page.newsletter_recipients.greeting|newsletter_richtext }}
              {% endif %}
          </mj-body>
      </mjml>
  {% endmrml %}


Campaign backends
-----------------

Wagtail-newsletter is designed to work with multiple email campaign providers,
though currently it only supports Mailchimp out of the box. Should you want to
target another provider, or change the behaviour of an existing backend (e.g.
to tweak the configuration of a campaign before it's sent to the API), you can
define your own backend class.

Backends should subclass the
``wagtail_newsletter.campaign_backends.CampaignBackend`` abstract class and
implement its methods.

To use a different backend, configure the ``WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND`` Django setting:

.. code-block:: python

  WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND = "myapp.CustomBackend"

Permissions
-----------

Out of the box, wagtail-newsletter checks the *Publish* permission to see
whether a user is allowed to perform newsletter actions. If the user doesn't
have the permission, they will not see the corresponding panels in the editor.

Permissions can be customized by implementing the
``has_newsletter_permission(user, action)`` method on the page model. It's
possible to selectively grant permissions to certain actions (a user might be
able to send themselves a test email but not send the campaign). Have a look at
`demo/models.py`_ for an example.

.. _demo/models.py: https://github.com/wagtail/wagtail-newsletter/blob/main/demo/models.py
