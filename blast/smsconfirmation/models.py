import logging
import random
import string

from django.db import models
from users.models import User
from users.signals import user_registered


logger = logging.getLogger(__name__)

CODE_CONFIRMATION_LEN = 4


def get_phone_confirmation_code():
    return ''.join([random.choice(string.digits) for _ in range(CODE_CONFIRMATION_LEN)])


class PhoneConfirmation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User)

    code = models.CharField(max_length=CODE_CONFIRMATION_LEN,
                            default=get_phone_confirmation_code)

    is_delivered = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)

    def is_actual(self):
        # TODO: Add test and implementation.
        return True

    class Meta:
        ordering = ('created_at',)


def on_user_registered(sender, **kwargs):
    logger.info('User has been registered. {} {} {}'.format(sender.pk, sender.country, sender.phone))
    PhoneConfirmation.objects.create(user=sender)

    # TODO (VM): Send sms message to user phone
    return

user_registered.connect(on_user_registered)