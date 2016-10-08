# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-10-08 11:39
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0035_auto_20161008_1133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pinnedposts',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pinners', to='posts.Post'),
        ),
        migrations.AlterField(
            model_name='pinnedposts',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pinned', to=settings.AUTH_USER_MODEL),
        ),
    ]