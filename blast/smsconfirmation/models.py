import logging
import random
import string

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import User


logger = logging.getLogger(__name__)

CODE_CONFIRMATION_LEN = 4


def get_phone_confirmation_code():
    return ''.join([random.choice(string.digits) for _ in range(CODE_CONFIRMATION_LEN)])


class PhoneConfirmationManager(models.Manager):

    def get_actual(self, phone, **kwargs):
        qs = self.get_queryset().filter(phone=phone, is_confirmed=False, **kwargs)
        qs = qs.order_by('-created_at')

        return qs.first()


class PhoneConfirmation(models.Model):
    REQUEST_PHONE = 1
    REQUEST_PASSWORD = 2
    REQUEST_CHANGE_PHONE = 3

    REQUEST_TYPES = (
        (REQUEST_PHONE, 'Phone confirmation'),
        (REQUEST_PASSWORD, 'Reset password'),
    )

    objects = PhoneConfirmationManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    phone = models.CharField(max_length=20)

    code = models.CharField(max_length=CODE_CONFIRMATION_LEN,
                            default=get_phone_confirmation_code)

    is_delivered = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)

    request_type = models.IntegerField(choices=REQUEST_TYPES)

    def __str__(self):
        return '{} {}'.format(self.phone, self.code)

    def is_actual(self):
        # TODO: Add test and implementation.
        return True

    class Meta:
        ordering = ('-created_at',)


@receiver(post_save, sender=PhoneConfirmation)
def post_confirmation(sender, instance, *args, **kwargs):
    from blast.celery import send_sms

    send_sms.delay(instance.phone, instance.code)
