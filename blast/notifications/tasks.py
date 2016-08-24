import blast.celery
import logging

from push_notifications.models import APNSDevice

from celery import shared_task


logger = logging.Logger(__name__)


@shared_task(bind=False)
def send_push_notification(user_id: int, message: str):
    logger.info('Send push notification to {} user'.format(user_id))

    devices = APNSDevice.objects.filter(user=user_id)
    devices.send_message(message)