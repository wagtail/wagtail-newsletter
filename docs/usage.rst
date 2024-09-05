Usage
=====

Edit and preview content
------------------------

Campaigns are sent from regular Wagtail pages that include the
``NewsletterPageMixin`` mixin. The content that you create for the Web is the
same content that will be sent in newsletter emails, albeit with different
formatting.

To help you make sure the content is right for emails, use Wagtail's editor
preview, and change *Preview mode* to *Newsletter*. It will show a preview of
what the email will look like in recipients' inboxes.

Send test email
---------------

Once you are happy with the content, it's a good idea to send yourself a test
email. Go over to the *Newsletter* tab in the editor and click *Send test
email*. This will save a page revision, upload the content to the campaign
provider (and create a new campaign if it hasn't been created already), then
trigger a test email from the campaign provider's system.

Send campaign
-------------

When you're ready to unleash the campaign upon your audience, click *Send
campaign* in the *Newsletter* editor tab. This will save a page revision,
upload the content to the campaign provider, and trigger campaign sending.

Schedule campaign
-----------------

If you'd like to send the campaign later, at a time when the emails are more
likely to be opened, you can click on *Schedule campaign* in the *Newsletter*
tab. If you're using the Mailchimp backend, make sure to select a time that is
a multiple of 15 minutes.

After a campaign is scheduled, and before it's time to send it, you can still
abort: click on the *Unschedule* button and the campaign will revert to a
draft.

Save campaign without sending
-----------------------------

If you want to simply upload the content to the campaign provider (without
sending a test email or triggering the campaign sending), maybe to make tweaks
to the campaign in the provider's app, or use advanced features like scheduled
sending, then click on *Save campaign to {provider}*. This will save a page
revision, and upload the campaign, but take no further action.

Keep in mind that any changes you make to the campaign will be overwritten if
you send a test email, or trigger campaign sending, from Wagtail.

View report
-----------

Once a campaign is sent, you can track its performance in the *Newsletter* tab
of the Wagtail admin page editor. It shows sending status, send time, how many
emails were sent, and how many people opened the message and clicked on a link.

Audit log
---------

Newsletter-related actions performed by users on a newsletter page are `logged
to the page history`_, just like regular save and publish actions. The following
actions are logged:

- :ref:`Save campaign <Save campaign without sending>`
- :ref:`Send test email`
- :ref:`Send campaign`

.. _logged to the page history: https://docs.wagtail.org/en/stable/extending/audit_log.html
