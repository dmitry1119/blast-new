import logging

from django.db import models
from users.models import User
from users.signals import user_registered


logger = logging.getLogger(__name__)


class PhoneConfirmation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User)

    is_delivered = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)


def on_user_registered(sender, **kwargs):
    logger.info('User has been registered. {} {} {}'.format(sender.pk, sender.country, sender.phone))
    confirmation = PhoneConfirmation.objects.create(user=sender)

    # TODO (VM): Send sms message to user phone
    return

user_registered.connect(on_user_registered)