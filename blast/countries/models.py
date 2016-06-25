from __future__ import unicode_literals

from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=6)

    class Meta:
        ordering = ('name',)