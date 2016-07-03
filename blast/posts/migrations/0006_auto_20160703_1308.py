# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-07-03 13:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20160703_1255'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('created_at',)},
        ),
        migrations.AddField(
            model_name='post',
            name='is_hidden',
            field=models.BooleanField(default=False),
        ),
    ]
