from __future__ import unicode_literals

from typing import Set, List

import logging
import os
import uuid
import redis

from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from core.decoratiors import memoize_posts
from countries.models import Country

r = redis.StrictRedis(host='localhost', port=6379, db=0)


def avatars_upload_dir(instance, filename):
    """Returns unique path for uploading image by user and filename"""
    name, ext = os.path.splitext(filename)
    filename = u'{}_{}{}'.format(instance.pk, str(uuid.uuid4()), ext)
    return u'/'.join([u'users', 'avatars', filename])


class UserManager(BaseUserManager):
    def create_user(self, phone, username, password, country=None):
        # TODO: Validate password and username
        user = self.model(phone=phone, username=username)
        user.country = country or Country.objects.get(name='Russia')
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)

        return user

    def create_superuser(self, phone, username, password):
        user = self.create_user(phone, username, password)
        user.is_admin = True
        user.is_superuser = True
        user.is_active = True

        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    GENDER_FEMALE = 0
    GENDER_MALE = 1

    GENDER = (
        (GENDER_FEMALE, 0),
        (GENDER_MALE, 1),
    )

    USERS_SET_KEY = 'users:set:all'  # Redis key for getting random users

    USERS_ZSET_KEY = 'users:zset:all'  # Redis key for getting users by popularity

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    phone = models.CharField(max_length=30, unique=True)
    email = models.EmailField(max_length=30, blank=True)

    country = models.ForeignKey(Country)

    # Profile information
    username = models.CharField(max_length=15, unique=True)
    fullname = models.CharField(max_length=50, blank=True)
    bio = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to=avatars_upload_dir, blank=True, null=True)
    website = models.CharField(max_length=50, blank=True)

    is_private = models.BooleanField(default=False,
                                     help_text='Is user account in private mode?')
    is_safe_mode = models.BooleanField(default=False)

    save_original_content = models.BooleanField(default=True)

    # Private information
    gender = models.IntegerField(default=None, blank=True, null=True,
                                 help_text='Use 1 for male and 0 for female')
    birthday = models.DateTimeField(default=None, blank=True, null=True)

    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    pinned_posts = models.ManyToManyField('posts.Post', blank=True,
                                          related_name='pinned_users')

    hidden_posts = models.ManyToManyField('posts.Post', blank=True,
                                          related_name='hidden_users')

    pinned_tags = models.ManyToManyField('tags.Tag', blank=True,
                                         related_name='pinned_users')

    # Filed for ranging
    popularity = models.FloatField(default=0)

    # FIXME: symmetrical=False?
    friends = models.ManyToManyField('User', blank=True, through='Follower',
                                     related_name='related_friends',
                                     through_fields=('follower', 'followee'))
    blocked = models.ManyToManyField('User', blank=True, through='BlockedUsers',
                                     related_name='blocked_users',
                                     through_fields=('user', 'blocked'))

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone']

    @staticmethod
    def redis_posts_key(pk: int):
        return u'user:{}:posts'.format(pk)

    @staticmethod
    @memoize_posts(u'user:{}:posts')
    def get_posts(user_id, start, end):
        from posts.models import Post
        user_posts = list(Post.objects.actual().filter(user=user_id))
        logging.info('Got {} posts for {} user key'.format(len(user_posts), user_id))

        result = []
        for it in user_posts:
            result.append(it.popularity)
            result.append(it.pk)

        return result

    def followers_count(self):
        # TODO (VM): Use cached value from Redis.
        return self.followers.count()

    def blasts_count(self):
        # TODO (VM): Use cached value from Redis.
        from posts.models import Post
        return Post.objects.filter(user=self.pk, expired_at__gte=timezone.now()).count()

    def following_count(self):
        # TODO (VM): Use cached value from Redis.
        return self.followees.count()

    def get_full_name(self):
        return self.fullname

    def get_short_name(self):
        return self.fullname

    @staticmethod
    def get_random_user_ids(count) -> Set[int]:
        if not r.exists(User.USERS_SET_KEY):
            # Heat up cache
            users = User.objects.all()
            users = [it.pk for it in users]

            r.sadd(User.USERS_SET_KEY, *users)

        items = r.srandmember(User.USERS_SET_KEY, count)
        return {int(it) for it in items}

    @staticmethod
    def get_most_popular_ids(start, end):
        if not r.exists(User.USERS_ZSET_KEY):
            # Heat up cache
            users = User.objects.all()
            # users = [it.pk for it in users]

            to_add = []
            for it in users:
                to_add.append(it.popularity)
                to_add.append(it.pk)

            if to_add:
                r.zadd(User.USERS_ZSET_KEY, *to_add)

        items = r.zrevrange(User.USERS_ZSET_KEY, start, end)
        return [int(it) for it in items]

    @staticmethod
    def get_users_count():
        if r.exists(User.USERS_ZSET_KEY):
            return r.zcard(User.USERS_ZSET_KEY)
        else:
            return 0

    @property
    def is_staff(self):
        return self.is_admin

    def str(self):
        return self.email


class Follower(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    follower = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='followees')
    followee = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='followers')

    def __str__(self):
        return u'{} to {}'.format(self.follower, self.followee)

    class Meta:
        unique_together = ('follower', 'followee')


# block user - it is for the purpose of not displaying content from that user on the newsfeed
# and also with comment notifications users who have been blocked will not be sent to the user
class BlockedUsers(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey('User', on_delete=models.CASCADE,
                             related_name='block_owner')

    blocked = models.ForeignKey('User', on_delete=models.CASCADE,
                                related_name='blocked_user')

    class Meta:
        unique_together = ('user', 'blocked')


class UserSettings(models.Model):
    """ List of user notify settings """
    OFF = 0
    PEOPLE_I_FOLLOW = 1
    EVERYONE = 2

    CHOICES = (
        (OFF, 0),
        (PEOPLE_I_FOLLOW, 1),
        (EVERYONE, 2)
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')

    notify_my_blasts = models.BooleanField(default=True)
    notify_upvoted_blasts = models.BooleanField(default=False)
    notify_downvoted_blasts = models.BooleanField(default=False)
    notify_pinned_blasts = models.BooleanField(default=False)

    notify_votes = models.BooleanField(default=True)

    notify_new_followers = models.IntegerField(choices=CHOICES, default=PEOPLE_I_FOLLOW)
    notify_comments = models.IntegerField(choices=CHOICES, default=PEOPLE_I_FOLLOW)
    notify_reblasts = models.IntegerField(choices=CHOICES, default=PEOPLE_I_FOLLOW)


@receiver(post_save, sender=User, dispatch_uid='users_post_user_save_handler')
def post_user_created(sender, instance: User, **kwargs):
    if not kwargs['created']:
        return

    # add user to set of all users.
    r.sadd(User.USERS_SET_KEY, instance.pk)
    r.zadd(User.USERS_ZSET_KEY, 1, instance.pk)

    # Creates settings for user
    UserSettings.objects.create(user=instance)


@receiver(post_save, sender=Follower, dispatch_uid='update_user_popularity_positive')
def update_user_popularity_positive(sender, instance: Follower, **kwargs):
    if not kwargs['created']:
        return

    followee_id = instance.followee_id
    r.zincrby(User.USERS_ZSET_KEY, followee_id, 1)

    User.objects.filter(pk=instance.followee_id).update(popularity=F('popularity') + 1)


@receiver(pre_delete, sender=Follower, dispatch_uid='update_user_popularity_negative')
def update_user_popularity_negative(sender, instance: Follower, **kwargs):
    followee_id = instance.followee_id
    r.zincrby(User.USERS_ZSET_KEY, followee_id, -1)

    User.objects.filter(pk=instance.followee_id).update(popularity=F('popularity') - 1)