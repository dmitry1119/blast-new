# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-07-16 17:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20160708_0831'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='is_anonymous',
            field=models.BooleanField(default=False),
        ),
    ]
