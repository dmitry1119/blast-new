# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-10-15 17:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0009_auto_20161011_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Started follow'), (1, 'Mentioned in comment'), (2, 'Votes reached'), (3, 'Ending soon: owner'), (4, 'Ending soon: pinner'), (5, 'Ending soon: upvoter'), (6, 'Ending soon: downvoter'), (7, 'Shared a blast'), (8, 'Shared a hashtag')]),
        ),
    ]
