from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from users.models import User


class Report(models.Model):
    OTHER = 0
    SENSITIVE_CONTENT = 1
    SPAM = 2
    DUPLICATED_CONTENT = 3
    BULLYING = 4
    INTEL_VIOLATION = 5

    REASONS = (
        (OTHER, "Other"),
        (SENSITIVE_CONTENT, "Sensitive content"),
        (SPAM, "Spam"),
        (DUPLICATED_CONTENT, "Duplicated content"),
        (BULLYING, "Bulling"),
        (INTEL_VIOLATION, "Intel violation"),
    )

    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User)
    reason = models.IntegerField(choices=REASONS, help_text='Report reason')
    text = models.CharField(max_length=128, blank=True, help_text='Details')

    content_type = models.ForeignKey(ContentType,
                                     related_name="content_type_set_for_%(class)s",
                                     on_delete=models.CASCADE)
    object_pk = models.PositiveIntegerField('object ID')
    content_object = GenericForeignKey('content_type', 'object_pk')

    class Meta:
        get_latest_by = "created_at"
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        unique_together = ("content_type", "object_pk")
