import re

from django.db import models

# Create your models here.
from django.db.models import F
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from posts.models import Post


class Tag(models.Model):
    """
    Hast tag for Post model
    """
    title = models.CharField(max_length=30, unique=True, primary_key=True)

    # Total count of posts for current tag.
    total_posts = models.PositiveIntegerField(default=0)

    def __str__(self):
        return u'{} - {}'.format(self.title, self.total_posts)


@receiver(post_save, sender=Post, dispatch_uid='post_save_post_handler')
def post_save_post(sender, **kwargs):
    if not kwargs['created']:
        return

    post = kwargs['instance']

    tags = post.get_tag_titles()

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