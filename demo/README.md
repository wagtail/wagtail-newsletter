# Wagtail Newsletter demo project

This is a minimal Wagtail project that exemplifies how to integrate `wagtail-newsletter` into a project.

## Running the demo project

From the top-level repository directory, run:

```
./demo/manage.py migrate
./demo/manage.py createcachetable
./demo/manage.py createsuperuser
./demo/manage.py runserver
```

Then open http://localhost:8000/ in your browser.
