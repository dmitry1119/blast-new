import os
import re
import uuid
from datetime import timedelta

from django.db import models
from django.db.models import F
from django.dispatch import receiver
from django.utils import timezone

from users.models import User
from django.db.models.signals import post_save, post_delete, pre_delete


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


class Tag(models.Model):
    """
    Hast tag for Post model
    """
    title = models.CharField(max_length=30, unique=True, primary_key=True)

    # Total count of posts for current tag.
    total_posts = models.PositiveIntegerField(default=0)

    def __str__(self):
        return u'{} - {}'.format(self.title, self.total_posts)


class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField(default=get_expiration_date)

    text = models.CharField(max_length=256, blank=True)

    user = models.ForeignKey(User, db_index=True)
    image = models.ImageField(upload_to=post_image_upload_dir, blank=True, null=True)
    video = models.FileField(upload_to=post_upload_dir, blank=True, null=True)

    is_anonymous = models.BooleanField(default=False)

    tags = models.ManyToManyField(Tag, blank=True)

    @property
    def time_remains(self):
        delta = self.expired_at - timezone.now()
        delta = delta - timedelta(microseconds=delta.microseconds)
        return delta

    def comments_count(self):
        # TODO (VM): Cache this value to redis
        return PostComment.objects.filter(post=self.pk).count()

    def downvoted_count(self):
        # TODO (VM): Cache this value to redis
        return PostVote.objects.filter(post=self.pk, is_positive=False).count()

    def votes_count(self):
        # TODO (VM): Cache this value to redis
        return PostVote.objects.filter(post=self.pk, is_positive=True).count()

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


@receiver(post_save, sender=Post, dispatch_uid='post_save_post_handler')
def post_save_post(sender, **kwargs):
    if not kwargs['created']:
        return

    post = kwargs['instance']

    reg = re.compile(r'(?:(?<=\s)|^)#(\w*[A-Za-z_]+\w*)', re.IGNORECASE)
    tags = reg.findall(post.text)

    if not tags:
        return

    db_tags = Tag.objects.filter(title__in=tags).values('title')
    db_tags = {it['title'] for it in db_tags}

    to_create = set(tags) - db_tags
    db_tags = []
    for it in to_create:
        db_tags.append(Tag(title=it))

    if db_tags:
        # FIXME (VM): if two user tries to create a same tags,
        #             it will throw exception for one of them.
        Tag.objects.bulk_create(db_tags)

    # Increase total posts counter
    Tag.objects.filter(title__in=tags).update(total_posts=F('total_posts') + 1)

    for it in tags:
        post.tags.add(it)


@receiver(pre_delete, sender=Post, dispatch_uid='pre_delete_post_handler')
def pre_delete_post(sender, **kwargs):
    # Decrease total posts counter
    post = kwargs['instance']
    post.tags.update(total_posts=F('total_posts') - 1)