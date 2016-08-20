import logging

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from posts.models import Post, PostComment
from users.models import User
from users.signals import start_following


logger = logging.getLogger(__name__)


class FollowRequest(models.Model):
    """ Follow request for private user """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    follower = models.ForeignKey(User, related_name='follower_requests', db_index=True)
    followee = models.ForeignKey(User, related_name='followee_requests', db_index=True)

    class Meta:
        unique_together = ('follower', 'followee',)


class Notification(models.Model):
    STARTED_FOLLOW_PATTERN = 'Started following you.'
    VOTES_REACHED_PATTERN = 'You blast reached {} votes.'
    MENTIONED_IN_COMMENT_PATTERN = 'Mentioned you in comment'

    STARTED_FOLLOW = 0
    MENTIONED_IN_COMMENT = 1
    VOTES_REACHED = 2

    TYPE = (
        (STARTED_FOLLOW, 'Started follow'),
        (MENTIONED_IN_COMMENT, 'Mentioned in comment'),
        (VOTES_REACHED, 'Votes reached')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    post = models.ForeignKey(Post, blank=True, null=True)
    user = models.ForeignKey(User, related_name='notifications', db_index=True)
    other = models.ForeignKey(User, null=True, blank=True, related_name='mention_notifications')

    text = models.CharField(max_length=128)
    type = models.PositiveSmallIntegerField(choices=TYPE)

# TODO: make tests.
@receiver(post_save, sender=PostComment, dispatch_uid='comment_notification')
def post_save_comment(sender, **kwargs):
    if not kwargs['created']:
        return

    instance = kwargs['instance']

    users = instance.get_notified_users()
    if not users:
        return

    query = Q()
    for it in users:
        query = query | Q(username__istartswith=it)

    users = User.objects.filter(query)
    notifications = []
    for it in users:
        notification = Notification(user=it, post=instance.post,
                                    other=instance.user,
                                    text=Notification.MENTIONED_IN_COMMENT_PATTERN,
                                    type=Notification.MENTIONED_IN_COMMENT)
        notifications.append(notification)

    Notification.objects.bulk_create(notifications)


@receiver(post_save, sender=Post, dispatch_uid='post_notification')
def post_save_post(sender, **kwargs):
    """Handles changing of votes counter and creates notification"""
    if not kwargs['created']:
        return

    instance = kwargs['instance']
    votes = instance.voted_count
    if votes == 0 or votes % 10:
        return

    if (votes <= 100 and votes % 10 == 0) or (votes >= 1000 and votes % 1000 == 0):
        logger.info('Post {} reached {} votes', instance, votes)
        Notification.objects.create(user=instance.user, post=instance,
                                    text=Notification.VOTES_REACHED_PATTERN.format(votes),
                                    type=Notification.VOTES_REACHED)


@receiver(start_following, dispatch_uid='post_follow_notification')
def start_following_handler(sender, **kwargs):
    """Handles following event"""
    followee = kwargs['followee']
    follower = kwargs['follower']

    logger.info('Create following notification {} {}'.format(follower, followee))
    Notification.objects.create(text=Notification.STARTED_FOLLOW_PATTERN,
                                user=followee, other=follower,
                                type=Notification.STARTED_FOLLOW)
