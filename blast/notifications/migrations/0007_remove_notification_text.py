# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-08-29 12:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0006_notification_post'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='text',
        ),
    ]
