import logging
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blast.settings')

from django.conf import settings

app = Celery('blast')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

logger = logging.getLogger(__name__)
