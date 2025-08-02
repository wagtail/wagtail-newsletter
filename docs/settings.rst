Settings
========

Wagtail-newsletter can be configured with the following :doc:`Django settings
<django:topics/settings>`.

Campaigns
---------

``WAGTAIL_NEWSLETTER_FROM_NAME``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  WAGTAIL_NEWSLETTER_FROM_NAME = "Bakery Tips"

When sending a newsletter, this value will appear as the email sender's name.

``WAGTAIL_NEWSLETTER_REPLY_TO``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  WAGTAIL_NEWSLETTER_FROM_NAME = "bakerytips@example.com"

When sending a newsletter, this value will appear as the email sender's
address. Be sure to configure your email domain to allow the newsletter service
to send emails on behalf of this address, otherwise they will likely be marked
as spam.

Backends
--------

``WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND = "wagtail_newsletter.campaign_backends.mailchimp.MailchimpCampaignBackend"

  # Or alternatively

  WAGTAIL_NEWSLETTER_CAMPAIGN_BACKEND = "wagtail_newsletter.campaign_backends.listmonk.ListmonkCampaignBackend"

Specifies which :ref:`campaign backend <Campaign backends>` to use.


``WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-us13"

When using the default Mailchimp backend, this setting specifies the API key.
An API key can be obtained `from the Mailchimp website`_.

.. _from the Mailchimp website: https://us1.admin.mailchimp.com/account/api/

``WAGTAIL_NEWSLETTER_LISTMONK_HEADERS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  WAGTAIL_NEWSLETTER_LISTMONK_HEADERS = {
      "Content-Type": "application/json",
      "charset": "utf-8"
  }

Optional. Specifies additional headers to include in requests to the listmonk API.
Defaults to ``{"Content-Type": "application/json;charset=utf-8"}``.

``WAGTAIL_NEWSLETTER_LISTMONK_BASE_URL``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  WAGTAIL_NEWSLETTER_LISTMONK_BASE_URL = "https://localhost:8000"

Specifies the base URL of your listmonk server. This should point to the root of the listmonk API.

``WAGTAIL_NEWSLETTER_LISTMONK_USER``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  WAGTAIL_NEWSLETTER_LISTMONK_USER = "user"

The username associated with your listmonk API key. This user must have the appropriate permissions to create and send campaigns.

``WAGTAIL_NEWSLETTER_LISTMONK_API_KEY``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  WAGTAIL_NEWSLETTER_LISTMONK_API_KEY = "the-listmonk-api-key"

The API key used to authenticate with the listmonk server.


Recipients
----------

``WAGTAIL_NEWSLETTER_RECIPIENTS_MODEL``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  WAGTAIL_NEWSLETTER_RECIPIENTS_MODEL = "wagtail_newsletter.NewsletterRecipients"

Specifies which :ref:`recipients model <Recipients model>` to use.

``WAGTAIL_NEWSLETTER_CACHE_TIMEOUT``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  WAGTAIL_NEWSLETTER_CACHE_TIMEOUT = 300  # 5 minutes

Specifies how long, in seconds, to cache information about recipients
(audiences, segments, and subscriber counts).
