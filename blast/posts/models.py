import logging
import redis
import os
import re
import uuid
from datetime import timedelta

from django.db.models import Q
from django.db import models
from django.db.models import F
from django.utils import timezone

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from users.models import User
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

logger = logging.getLogger(__name__)
r = redis.StrictRedis(host='localhost', port=6379, db=0)



def post_image_upload_dir(instance: User, filename: str):
    """Returns unique path for uploading image by user and filename"""
    name, ext = os.path.splitext(filename)
    filename = u'{}{}'.format(str(uuid.uuid4()), ext)
    return u'/'.join([u'user', u'images', filename])


def post_upload_dir(instance, filename: str):
    """Returns unique path for uploading image by user and filename"""
    name, ext = os.path.splitext(filename)
    filename = u'{}{}'.format(str(uuid.uuid4()), ext)
    return u'/'.join([u'user', u'videos', filename])


def get_expiration_date():
    return timezone.now() + timedelta(days=1)


USER_REG = reg = re.compile(r'(?:(?<=\s)|^)@(\w*[A-Za-z_]+\w*)', re.IGNORECASE)


def get_notified_users(text: str):
    """returns list of users notified by @"""
    return USER_REG.findall(text)


class PostManager(models.Manager):
    def actual(self):
        return self.get_queryset().filter(expired_at__gte=timezone.now())

    def public(self):
        qs = self.get_queryset()
        qs = qs.filter(Q(user__is_private=False) | Q(user=None),
                       expired_at__gte=timezone.now())

        return qs

    def expired(self):
        qs = self.get_queryset()
        qs = qs.filter(expired_at__lt=timezone.now())

        return qs


class Post(models.Model):

    objects = PostManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField(default=get_expiration_date)

    text = models.CharField(max_length=256, blank=True)

    # TODO: Remove black, null.
    user = models.ForeignKey(User, db_index=True, blank=True, null=True)
    image = models.ImageField(upload_to=post_image_upload_dir, blank=True, null=True)
    video = models.FileField(upload_to=post_upload_dir, blank=True, null=True)

    image_135 = ImageSpecField(source='image',
                               processors=[ResizeToFill(135, 135)],
                               format='PNG',
                               options={'quality': 90})

    image_248 = ImageSpecField(source='image',
                               processors=[ResizeToFill(248, 248)],
                               format='PNG',
                               options={'quality': 90})

    tags = models.ManyToManyField('tags.Tag', blank=True)

    # Cache for voted and downvoted lists.
    downvoted_count = models.PositiveIntegerField(default=0)
    voted_count = models.PositiveIntegerField(default=0)

    @property
    def is_anonymous(self):
        return self.user_id == User.objects.anonymous_id

    @property
    def popularity(self):
        return self.voted_count - self.downvoted_count

    def get_tag_titles(self):
        expr = re.compile(r'(?:(?<=\s)|^)#(\w*[A-Za-z_]+\w*)', re.IGNORECASE)
        return expr.findall(self.text)

    @property
    def time_remains(self):
        delta = self.expired_at - timezone.now()
        delta = delta - timedelta(microseconds=delta.microseconds)  # Remove microseconds for pretty printing
        return delta

    @property
    def notified_users(self):
        return get_notified_users(self.text)

    def comments_count(self):
        # TODO (VM): Cache this value to redis
        return PostComment.objects.filter(post=self.pk).count()

    def save(self, **kwargs):
        if not self.user:
            self.user_id = User.objects.anonymous_id

        return super().save(**kwargs)

    def __str__(self):
        return u'{} {}'.format(self.id, self.user_id)

    class Meta:
        ordering = ('-created_at',)


class PostVote(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User, db_index=True)
    post = models.ForeignKey(Post, db_index=True)
    is_positive = models.NullBooleanField()  # False if post is downvoted, True otherwise.

    def __str__(self):
        return u'{} {}'.format(self.pk, self.user_id, self.post_id)

    class Meta:
        unique_together = (('user', 'post'),)


class PostComment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    parent = models.ForeignKey('PostComment', db_index=True,
                               blank=True, null=True)
    user = models.ForeignKey(User, db_index=True)
    post = models.ForeignKey(Post, db_index=True)
    text = models.CharField(max_length=256)

    def replies_count(self):
        # TODO (VM): Add redis cache
        return PostComment.objects.filter(parent=self.pk).count()

    @property
    def notified_users(self):
        return get_notified_users(self.text)

    def __str__(self):
        return u'{} for post {}'.format(self.pk, self.post)


class PostReport(models.Model):
    OTHER = 0
    SENSITIVE_CONTENT = 1
    SPAM = 2
    DUPLICATED_CONTENT = 3
    BULLYING = 4
    INTEL_VIOLATION = 5

    REASONS = (
        (OTHER, 0),
        (SENSITIVE_CONTENT, 1),
        (SPAM, 2),
        (DUPLICATED_CONTENT, 3),
        (BULLYING, 4),
        (INTEL_VIOLATION, 5),
    )

    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User)
    post = models.ForeignKey(Post)

    reason = models.IntegerField(choices=REASONS,
                                 help_text='Report reason')
    text = models.CharField(max_length=128, blank=True,
                            help_text='Details')


USERS_RANGES_COUNT = 4


@receiver(pre_delete, sender=Post, dispatch_uid='posts_pre_delete')
def pre_delete_post(sender, instance: Post, **kwargs):
    logging.info('pre_delete for {} post'.format(instance.pk))
    if instance.video:
        logger.info('Delete {} image of {} post'.format(instance.image, instance.pk))
        instance.video.delete()

    if instance.image:
        logger.info('Delete {} video of {} post'.format(instance.image, instance.pk))
        instance.image.delete()

    # Remove post from user post set.
    posts_key = User.redis_posts_key(instance.user_id)
    if r.exists(posts_key):  # If cache is "hot"
        r.zrem(posts_key, instance.pk)
        logging.info('Remove {} from {} cache'.format(instance.pk, posts_key))

    # Updates search range
    search_range = min(r.zcard(posts_key), USERS_RANGES_COUNT)
    User.objects.filter(pk=instance.user_id).update(search_range=search_range)

    # Updates user popularity
    User.objects.filter(pk=instance.user_id).update(popularity=F('popularity') - 1)


@receiver(post_save, sender=Post, dispatch_uid='posts_post_save')
def post_save_post(sender, instance: Post, **kwargs):
    if not kwargs['created']:
        return

    # Add post to user post set.
    posts_key = User.redis_posts_key(instance.user_id)
    if not r.exists(posts_key):
        User.get_posts(instance.user_id, 0, 1)  # Heat up cache

    r.zadd(posts_key, 1, instance.pk)
    logging.info('Add {} to {} cache'.format(instance.pk, posts_key))

    # Updates search popularity
    search_range = min(r.zcard(posts_key), USERS_RANGES_COUNT)
    User.objects.filter(pk=instance.user_id).update(search_range=search_range)

    # Updates user popularity
    User.objects.filter(pk=instance.user_id).update(popularity=F('popularity') + 1)


@receiver(post_save, sender=PostVote, dispatch_uid='posts_post_save_vote_handler')
def post_save_vote(sender, **kwargs):
    instance = kwargs['instance']

    if instance.is_positive is None:
        return

    user_key = User.redis_posts_key(instance.post.user_id)
    if instance.is_positive:
        r.zincrby(user_key, instance.post_id, 1)  # incr post in redis cache
        Post.objects.filter(pk=instance.post.pk).update(voted_count=F('voted_count') + 1)
    else:
        r.zincrby(user_key, instance.post_id, -1)  # incr post in redis cache
        Post.objects.filter(pk=instance.post.pk).update(downvoted_count=F('downvoted_count') + 1)
