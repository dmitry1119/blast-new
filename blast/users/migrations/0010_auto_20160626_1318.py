# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-06-26 13:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_remove_user_is_confirm'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='bio',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='is_safe_mode',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='save_original_content',
            field=models.BooleanField(default=True),
        ),
    ]