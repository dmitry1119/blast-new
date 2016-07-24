# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-07-24 16:28
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_user_followers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='followers',
            field=models.ManyToManyField(blank=True, related_name='followees', to=settings.AUTH_USER_MODEL),
        ),
    ]
