# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-07-20 16:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_post_is_anonymous'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.CharField(blank=True, max_length=256),
        ),
    ]
