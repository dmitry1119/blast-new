# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-08-29 12:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0007_remove_notification_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='votes',
            field=models.PositiveIntegerField(default=0),
        ),
    ]