import blast.celery
import logging

from push_notifications.apns import apns_send_bulk_message
from push_notifications.models import APNSDevice

from celery import shared_task


logger = logging.Logger(__name__)


@shared_task(bind=False)
def send_push_notification(user_id: int, message: str, payload: dict):
    logger.info(u'Send push notification to {} user with {}'.format(user_id, payload))

    devices = APNSDevice.objects.filter(user=user_id)
    devices.send_message(message, sound='default', extra=payload)


@shared_task(bind=False)
def send_push_notification_to_device(registration_ids, message):
    logger.info(u'Send push notification to {} device with {}'.format(registration_ids, message))
    apns_send_bulk_message(registration_ids=registration_ids, alert=message)
