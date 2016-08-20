# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-08-19 07:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0024_auto_20160815_1255'),
        ('notifications', '0005_auto_20160816_1150'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='posts.Post'),
        ),
    ]
