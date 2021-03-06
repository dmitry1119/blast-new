# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-01-12 16:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FollowRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_seen', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('-id',),
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('votes', models.PositiveIntegerField(default=0)),
                ('type', models.PositiveSmallIntegerField(choices=[(0, 'Started follow'), (1, 'Mentioned in comment'), (2, 'Votes reached'), (3, 'Ending soon: owner'), (4, 'Ending soon: pinner'), (5, 'Ending soon: upvoter'), (6, 'Ending soon: downvoter'), (7, 'Shared a Blast'), (8, 'Shared a hashtag'), (9, 'Commented post'), (10, 'Marked for removal'), (11, 'Replied on comment')])),
                ('is_seen', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('-id',),
            },
        ),
    ]
