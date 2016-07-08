# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-07-08 08:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20160708_0831'),
        ('users', '0015_auto_20160706_1522'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='pinned_posts',
            field=models.ManyToManyField(related_name='users', to='posts.Post'),
        ),
    ]
