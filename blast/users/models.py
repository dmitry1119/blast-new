from __future__ import unicode_literals

import os
import uuid
from django.core.exceptions import ValidationError

from django.db import models

from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from countries.models import Country


def avatars_upload_dir(instance, filename):
    """Returns unique path for uploading image by user and filename"""
    name, ext = os.path.splitext(filename)
    filename = u'{}_{}{}'.format(instance.pk, str(uuid.uuid4()), ext)
    return u'/'.join([u'users', 'avatars', filename])


class UserManager(BaseUserManager):
    def create_user(self, phone, username, password):
        # TODO: Validate password and username
        user = self.model(phone=phone, username=username)
        user.country = Country.objects.get(name='Russia')
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    phone = models.CharField(max_length=30, unique=True)
    email = models.EmailField(max_length=30, blank=True)

    country = models.ForeignKey(Country)

    # Profile information
    username = models.CharField(max_length=15, unique=True)
    fullname = models.CharField(max_length=50, blank=False)
    bio = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to=avatars_upload_dir, blank=True)
    website = models.CharField(max_length=50, blank=True)

    is_private = models.BooleanField(default=False)
    is_safe_mode = models.BooleanField(default=False)

    save_original_content = models.BooleanField(default=True)

    # Private information
    gender = models.IntegerField(default=None, blank=True, null=True)
    birthday = models.DateTimeField(default=None, blank=True, null=True)

    # Internal information
    is_verified = models.BooleanField(default=False)  # Is phone confirmed?

    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']

    def clean(self):
        if not self.username or len(self.username) > self._meta.fields['username'].max_length:
            raise ValidationError({'username': 'Your username must be 15 characters or less'})

        return super().clean()

    def followers_count(self):
        # TODO: Use cached value from Redis.
        import random
        return random.randint(0, 100000)

    def get_full_name(self):
        return self.fullname

    def get_short_name(self):
        return self.fullname

    @property
    def is_staff(self):
        return self.is_admin

    def str(self):
        return self.email


# class NotifySettings(models.Model):
#     """List of notify settings"""
#     OFF = 0
#     PEOPLE_I_FOLLOW = 1
#     EVERYONE = 2
#
#     CHOICES = (
#         (OFF, 0),
#         (PEOPLE_I_FOLLOW, 1),
#         (EVERYONE, 2)
#     )
#
#     notify_my_blasts = models.BooleanField(default=True)
#     notify_upvoted_blasts = models.BooleanField(default=False)
#     notify_downvoted_blasts = models.BooleanField(default=False)
#     notify_pinned_blasts = models.BooleanField(default=False)
#
#     notify_votes = models.BooleanField(default=True)
#
#     comments = models.IntegerField(choices=CHOICES)
#     reblasts = models.IntegerField(choices=CHOICES)
