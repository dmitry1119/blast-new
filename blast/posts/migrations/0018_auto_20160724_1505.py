# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-07-24 15:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0017_auto_20160724_1446'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(blank=True, to='posts.Tag'),
        ),
    ]