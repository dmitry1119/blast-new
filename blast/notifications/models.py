import logging

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from posts.models import Post, PostComment
from tags.models import Tag
from users.models import User, UserSettings, Follower

from notifications.tasks import send_push_notification

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
    TEXT_STARTED_FOLLOW_PATTERN = '{} started following you'
    TEXT_VOTES_REACHED_PATTERN = 'You blast reached {} votes'
    TEXT_MENTIONED_IN_COMMENT_PATTERN = '{} mentioned you in comment'

    TEXT_END_SOON_OWNER = 'Your Blast is ending soon'
    TEXT_END_SOON_PINNER = 'Pinned Blast ending soon'
    TEXT_END_SOON_UPVOTER = 'Upvoted Blast ending soon'
    TEXT_END_SOON_DOWNVOTER = 'Downvoted Blast ending soon'

    TEXT_SHARE_POST = 'Shared a Blast'
    TEXT_SHARE_TAG = 'Shared a hashtag: #{}'


    STARTED_FOLLOW = 0
    MENTIONED_IN_COMMENT = 1
    VOTES_REACHED = 2
    ENDING_SOON_OWNER = 3
    ENDING_SOON_PINNER = 4
    ENDING_SOON_UPVOTER = 5
    ENDING_SOON_DOWNVOTER = 6

    SHARE_POST = 7
    SHARE_TAG = 8

    TYPE = (
        (STARTED_FOLLOW, 'Started follow'),
        (MENTIONED_IN_COMMENT, 'Mentioned in comment'),
        (VOTES_REACHED, 'Votes reached'),
        (ENDING_SOON_OWNER, 'Ending soon: owner'),
        (ENDING_SOON_PINNER, 'Ending soon: pinner'),
        (ENDING_SOON_UPVOTER, 'Ending soon: upvoter'),
        (ENDING_SOON_DOWNVOTER, 'Ending soon: downvoter'),
        (SHARE_POST, "Shared a blast"),
        (SHARE_TAG, "Shared a hashtag"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    votes = models.PositiveIntegerField(default=0)
    post = models.ForeignKey(Post, blank=True, null=True)
    user = models.ForeignKey(User, related_name='notifications', db_index=True)
    tag = models.ForeignKey(Tag, blank=True, null=True)
    other = models.ForeignKey(User, null=True, blank=True, related_name='mention_notifications')

    type = models.PositiveSmallIntegerField(choices=TYPE)

    @property
    def text(self):
        if self.type == Notification.STARTED_FOLLOW:
            return Notification.TEXT_STARTED_FOLLOW_PATTERN.format(self.other.username)
        elif self.type == Notification.VOTES_REACHED:
            return Notification.TEXT_VOTES_REACHED_PATTERN.format(self.votes)
        elif self.type == Notification.MENTIONED_IN_COMMENT:
            return Notification.TEXT_MENTIONED_IN_COMMENT_PATTERN.format(self.other.username)

        elif self.type == Notification.ENDING_SOON_OWNER:
            return self.TEXT_END_SOON_OWNER
        elif self.type == Notification.ENDING_SOON_PINNER:
            return self.TEXT_END_SOON_PINNER
        elif self.type == Notification.ENDING_SOON_UPVOTER:
            return self.TEXT_END_SOON_UPVOTER
        elif self.type == Notification.ENDING_SOON_DOWNVOTER:
            return self.TEXT_END_SOON_DOWNVOTER

        elif self.type == Notification.SHARE_POST:
            return self.TEXT_SHARE_POST
        elif self.type == Notification.SHARE_TAG:
            return self.TEXT_SHARE_TAG.format(self.tag_id)

        logger.error('Unknown notification type')

        raise ValueError('Unknown notification type')

    @property
    def push_payload(self):
        return {
            'sound': 'default',
            'tagId': self.tag_id,
            'postId': self.post_id,
            'userId': self.other_id,
        }

    def __str__(self):
        return '{} - {}'.format(self.user, self.text)


def notify_users(users: list, post: Post, author: User):
    # TODO: author can be None
    if not users:
        return

    query = Q()
    for it in users:
        query = query | Q(username__istartswith=it)

    users = User.objects.filter(query).prefetch_related('settings')

    followers = Follower.objects.filter(followee=author, follower__in=users)
    followers = {it.follower_id for it in followers}

    notifications = []
    for it in users:
        is_follow = it.id in followers
        if it.settings.notify_comments == UserSettings.OFF:
            continue

        for_everyone = it.settings.notify_comments == UserSettings.EVERYONE
        for_follower = (it.settings.notify_comments == UserSettings.PEOPLE_I_FOLLOW and is_follow)
        if for_everyone or for_follower:
            notification = Notification(user=it, post=post, other=author,
                                        type=Notification.MENTIONED_IN_COMMENT)
            notifications.append(notification)

    Notification.objects.bulk_create(notifications)

    for it in notifications:
        send_push_notification.delay(it.user_id, it.text, it.push_payload)


@receiver(post_save, sender=PostComment, dispatch_uid='notifications_comments')
def post_save_comment(sender, **kwargs):
    if not kwargs['created']:
        return

    instance = kwargs['instance']

    users = instance.notified_users
    notify_users(users, instance.post, instance.user)


@receiver(post_save, sender=Post, dispatch_uid='notifications_posts')
def post_save_post(sender, instance: Post, **kwargs):
    """Handles changing of votes counter and creates notification"""
    if not kwargs['created']:
        return

    votes = instance.voted_count

    users = instance.notified_users
    notify_users(users, instance, instance.user)

    if votes == 0 or votes % 10:
        return

    if (votes <= 100 and votes % 10 == 0) or (votes >= 1000 and votes % 1000 == 0):
        logger.info('Post {} reached {} votes'.format(instance, votes))
        notification = Notification.objects.create(user=instance.user, post_id=instance.pk,
                                                   votes=votes, type=Notification.VOTES_REACHED)
        send_push_notification.delay(instance.user_id, notification.text,
                                     notification.push_payload)


@receiver(post_save, sender=Follower, dispatch_uid='notifications_follow')
def start_following_handler(sender, instance: Follower, **kwargs):
    """Handles following event"""
    followee = instance.followee_id
    follower = instance.follower_id

    if followee == User.objects.anonymous_id:
        # Ignore anonymous user because he followee by default
        return

    logger.info('Create following notification {} {}'.format(follower, followee))
    notification = Notification.objects.create(user_id=followee, other_id=follower,
                                               type=Notification.STARTED_FOLLOW)
    send_push_notification.delay(followee, notification.text, notification.push_payload)
