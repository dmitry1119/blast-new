# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-08-16 09:47
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_followrequest'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='followrequest',
            name='followee',
        ),
        migrations.RemoveField(
            model_name='followrequest',
            name='follower',
        ),
        migrations.DeleteModel(
            name='FollowRequest',
        ),
    ]
