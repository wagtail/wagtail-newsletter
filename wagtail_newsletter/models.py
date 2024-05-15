from django.db import models


class NewsletterRecipientsBase(models.Model):
    name = models.CharField(max_length=1000)
    audience = models.CharField(max_length=1000)
    segment = models.CharField(max_length=1000, blank=True, null=True)  # noqa: DJ001

    class Meta:  # type: ignore
        abstract = True

    def __str__(self):
        return self.name


class NewsletterRecipients(NewsletterRecipientsBase):
    class Meta:  # type: ignore
        verbose_name_plural = "Newsletter recipients"
