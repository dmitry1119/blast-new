# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-07-29 12:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0018_auto_20160724_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='postcomment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='posts.PostComment'),
        ),
    ]
