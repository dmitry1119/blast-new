import logging
import re
import redis

from django.db import models

# Create your models here.
from django.db.backends.dummy.base import IntegrityError
from django.db.models import F
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from core.decorators import save_to_zset
from posts.models import Post


logger = logging.Logger(__name__)
r = redis.StrictRedis(host='localhost', port=6379, db=0)


class Tag(models.Model):
    """
    Hast tag for Post model
    """
    title = models.CharField(max_length=30, unique=True, primary_key=True)

    # Total count of posts for current tag.
    total_posts = models.PositiveIntegerField(default=0)

    def posts_count(self):
        return Post.objects.filter(tags__title=self.title).count()
        # key = r.zcard(Tag.redis_posts_key(self.pk))
        # if not r.exists(key):
        #     posts = Post.objects.filter(tags__title=self.title).values_list('id', flat=True)
        #     result = []
        #     for it in posts:
        #         result.append(1)
        #         result.append(it)
        #     if result:
        #         r.zadd(key, *result)
        #
        # return r.zcard(key)

    @staticmethod
    def redis_posts_key(pk):
        return u'tag:{}:posts'.format(pk)

    @staticmethod
    @save_to_zset(u'tag:{}:posts')
    def get_posts(tag_pk, start, end):
        result = []
        posts = list(Post.objects.actual().filter(tags=tag_pk))
        for it in posts:
            result.append(it.popularity)
            result.append(it.pk)

        return result

    def __str__(self):
        return u'{} - {}'.format(self.title, self.total_posts)


@receiver(pre_delete, sender=Tag, dispatch_uid='pre_deleted_tag')
def pre_delete_tag(sender, instance, **kwargs):
    r.delete(Tag.redis_posts_key(pk=instance.title))


@receiver(post_save, sender=Post, dispatch_uid='post_save_tags_handler')
def post_save_post(sender, instance, **kwargs):
    if not kwargs['created']:
        return

    tags = instance.get_tag_titles()

    logger.info('Created new post with {} tags'.format(tags))

    if not tags:
        return

    db_tags = Tag.objects.filter(title__in=tags)
    db_tags = {it.title for it in db_tags}
    to_create = set(tags) - db_tags

    db_tags = []
    for it in to_create:
        db_tags.append(Tag(title=it))

    if db_tags:
        # FIXME (VM): if two user tries to create a same tags,
        # it will throw exception for one of them.
        Tag.objects.bulk_create(db_tags)

    db_tags = list(Tag.objects.filter(title__in=tags))
    instance.tags.add(*db_tags)

    # Increase total posts counter
    for it in db_tags:
        key = Tag.redis_posts_key(it.title)
        r.zincrby(key, instance.pk)

    Tag.objects.filter(title__in=tags).update(total_posts=F('total_posts') + 1)


@receiver(pre_delete, sender=Post, dispatch_uid='pre_deleted_post_tags_handler')
def pre_delete_post(sender, instance, **kwargs):
    tags = list(instance.tags.all())
    tags = {it.title for it in tags}
    logging.info('pre_delete: Post. Update tag counters. {}'.format(tags))
    for it in tags:
        key = Tag.redis_posts_key(it)
        logging.info('pre_delete: Post. Update tag {} with key {}'.format(it, key))
        r.zrem(key, instance.pk)

    try:
        Tag.objects.filter(title__in=tags).update(total_posts=F('total_posts') - 1)
    except IntegrityError as e:
        logger.error('{}'.format(e))
