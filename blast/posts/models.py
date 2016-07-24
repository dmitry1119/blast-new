import os
import re
import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone

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


class Tag(models.Model):
    """
    Hast tag for Post model
    """
    title = models.CharField(max_length=30, unique=True, primary_key=True)

    def __str__(self):
        return self.title


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

    def comments_count(self):
        # TODO (VM): Cache this value to redis
        return PostComment.objects.filter(post=self.pk).count()

    def downvoted_count(self):
        # TODO (VM): Cache this value to redis
        return PostVote.objects.filter(post=self.pk, is_positive=False).count()

    def votes_count(self):
        # TODO (VM): Cache this value to redis
        return PostVote.objects.filter(post=self.pk, is_positive=True).count()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        reg_expression = re.compile(r'(?:(?<=\s)|^)#(\w*[A-Za-z_]+\w*)', re.IGNORECASE)
        tags = reg_expression.findall(self.text)
        if not tags:
            return

        db_tags = Tag.objects.filter(title__in=tags).values('title')
        db_tags = {it['title'] for it in db_tags}

        to_create = set(tags) - db_tags
        db_tags = []
        for it in to_create:
            db_tags.append(Tag(title=it))

        # FIXME (VM): if two user tries to create a same tags,
        #             it will throw exception for one of them.
        Tag.objects.bulk_create(db_tags)

        for it in tags:
            self.tags.add(it)

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

    user = models.ForeignKey(User, db_index=True)
    post = models.ForeignKey(Post, db_index=True)
    text = models.CharField(max_length=256)


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
