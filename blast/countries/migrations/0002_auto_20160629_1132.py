# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-06-29 11:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('countries', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='country',
            name='code',
            field=models.CharField(max_length=10),
        ),
    ]
