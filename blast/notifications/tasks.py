from typing import List

from blast import celery
import logging

from push_notifications.apns import apns_send_bulk_message
from push_notifications.models import APNSDevice

from celery import shared_task

from users.models import Follower

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


@celery.app.task
def send_share_notifications(user_id: int, users: List, post_id: int = None, tag: str = None):
    from notifications.models import Notification

    if not users:
        logger.info('send_share_notifications: users is empty')
        return

    logger.info(u'Share %s by (%s, %s) to %s', user_id, post_id, tag, users)

    users = Follower.objects.filter(followee=user_id, follower_id__in=users)
    users = users.values_list('follower_id', flat=True)

    if not users:
        logger.info('send_share_notifications: users list is empty %s', users)
        return

    notification_type = None
    if post_id:
        notification_type = Notification.SHARE_POST
    elif tag:
        notification_type = Notification.SHARE_TAG

    # Create notifications
    notifications = []
    for user_id in users:
        instance = Notification(post_id=post_id, user_id=user_id, tag_id=tag,
                                other_id=user_id, type=notification_type)
        notifications.append(instance)

    Notification.objects.bulk_create(notifications)

    # Send messages
    logger.info('Send share push message %s %s %s %s', user_id, post_id, tag, users)
    notification = notifications[0]
    devices = APNSDevice.objects.filter(user_id__in=users)
    devices.send_message(notification.text, extra=notification.push_payload)
