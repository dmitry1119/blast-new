# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-07-16 15:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_auto_20160711_1442'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='notify_new_followers',
            field=models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=1),
        ),
    ]