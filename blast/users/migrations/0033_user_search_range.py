# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-09-11 17:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_auto_20160906_1525'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='search_range',
            field=models.SmallIntegerField(default=0),
        ),
    ]