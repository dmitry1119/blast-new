import os
import re
import uuid
from datetime import timedelta

from django.db import models
from django.db.models import F
from django.utils import timezone

from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import User


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


class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField(default=get_expiration_date)

    text = models.CharField(max_length=256, blank=True)

    user = models.ForeignKey(User, db_index=True)
    image = models.ImageField(upload_to=post_image_upload_dir, blank=True, null=True)
    video = models.FileField(upload_to=post_upload_dir, blank=True, null=True)

    is_anonymous = models.BooleanField(default=False)

    tags = models.ManyToManyField('tags.Tag', blank=True)

    # Cache for voted and downvoted lists.
    # Uses for
    downvoted_count = models.PositiveIntegerField(default=0)
    voted_count = models.PositiveIntegerField(default=0)

    def get_tag_titles(self):
        reg = re.compile(r'(?:(?<=\s)|^)#(\w*[A-Za-z_]+\w*)', re.IGNORECASE)
        return reg.findall(self.text)

    @property
    def time_remains(self):
        delta = self.expired_at - timezone.now()
        delta = delta - timedelta(microseconds=delta.microseconds)
        return delta

    def comments_count(self):
        # TODO (VM): Cache this value to redis
        return PostComment.objects.filter(post=self.pk).count()

    def __str__(self):
        return u'{}'.format(self.id)

    class Meta:
        ordering = ('-created_at',)


class PostVote(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User, db_index=True)
    post = models.ForeignKey(Post, db_index=True)
    is_positive = models.NullBooleanField()  # False if post is downvoted, True otherwise.

    class Meta:
        unique_together = (('user', 'post'),)


@receiver(post_save, sender=PostVote, dispatch_uid='post_save_vote_handler')
def post_save_vote(sender, **kwargs):
    # if not kwargs['created']:
    # TODO: update post instance by refreshing cache from db?
    # pass

    instance = kwargs['instance']

    if instance.is_positive is None:
        return

    if instance.is_positive:
        Post.objects.filter(pk=instance.post.pk).update(voted_count=F('voted_count') + 1)
    else:
        Post.objects.filter(pk=instance.post.pk).update(downvoted_count=F('downvoted_count') + 1)


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
