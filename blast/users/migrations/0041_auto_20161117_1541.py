# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-11-17 15:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0040_auto_20161029_1455'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersettings',
            name='notify_comments',
            field=models.IntegerField(choices=[(0, 'Off'), (1, 'People I follow'), (2, 'Everyone')], default=2),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='notify_downvoted_blasts',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='notify_new_followers',
            field=models.IntegerField(choices=[(0, 'Off'), (1, 'People I follow'), (2, 'Everyone')], default=2),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='notify_pinned_blasts',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='notify_reblasts',
            field=models.IntegerField(choices=[(0, 'Off'), (1, 'People I follow'), (2, 'Everyone')], default=2),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='notify_upvoted_blasts',
            field=models.BooleanField(default=True),
        ),
    ]