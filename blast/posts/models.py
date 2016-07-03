import os, uuid

from django.db import models
from users.models import User


def post_image_upload_dir(instance: User, filename: str):
    """Returns unique path for uploading image by user and filename"""
    name, ext = os.path.splitext(filename)
    filename = u'{}_{}{}'.format(instance.pk, str(uuid.uuid4()), ext)
    return u'/'.join([u'user', u'images', filename])


def post_upload_dir(instance: User, filename: str):
    """Returns unique path for uploading image by user and filename"""
    name, ext = os.path.splitext(filename)
    filename = u'{}_{}{}'.format(instance.pk, str(uuid.uuid4()), ext)
    return u'/'.join([u'user', u'videos', filename])


class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    text = models.CharField(max_length=256)

    user = models.ForeignKey(User)
    video = models.FileField(upload_to=post_upload_dir)

    is_hidden = models.BooleanField(default=False)

    def comments_count(self):
        # TODO (VM): Cache this value to redis
        return PostComment.objects.filter(post=self.pk).count()

    def downvoted_count(self):
        # TODO (VM): Cache this value to redis
        return PostVote.objects.filter(post=self.pk, is_positive=False).count()

    def votes_count(self):
        # TODO (VM): Cache this value to redis
        return PostVote.objects.filter(post=self.pk, is_positive=True).count()

    class Meta:
        ordering = ('-created_at',)


class PostVote(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User)
    post = models.ForeignKey(Post)
    is_positive = models.NullBooleanField() # False if post is downvoted, True otherwise.

    class Meta:
        unique_together = (('user', 'post'),)


class PostComment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User)
    post = models.ForeignKey(Post)
    text = models.CharField(max_length=256)