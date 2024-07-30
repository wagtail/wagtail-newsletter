# Wagtail Newsletter demo project

This is a minimal Wagtail project that exemplifies how to integrate `wagtail-newsletter` into a project. It includes:
- A page model, `demo.ArticlePage`, that is configured as a newsletter.
- A custom permission to restrict newsletter actions, `demo.sendnewsletter_articlepage`.
- A moderately complex newsletter template, `templates/demo/article_page_newsletter.html`.
- A custom recipients model, `demo.CustomRecipients`.

## Running the demo project

Get an [API key from Mailchimp](https://us1.admin.mailchimp.com/account/api/).

From the top-level repository directory, run:

```bash
export WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-us13
export WAGTAIL_NEWSLETTER_FROM_NAME="My Newsletter"
export WAGTAIL_NEWSLETTER_REPLY_TO=sender@example.com

python -m pip install --editable='.[testing,mailchimp,mrml]'
./demo/manage.py migrate
./demo/manage.py createcachetable
./demo/manage.py createsuperuser
./demo/manage.py runserver
```

Then open http://localhost:8000/ in your browser.
