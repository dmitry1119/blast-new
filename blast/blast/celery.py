import os, logging

from sinchsms import SinchSMS
from celery import Celery, shared_task

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blast.settings')

from django.conf import settings

app = Celery('blast')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

logger = logging.getLogger(__name__)


@shared_task(bind=False)
def send_sms(number, text):
    client = SinchSMS(app_key=settings.SINCH['APP_KEY'],
                      app_secret=settings.SINCH['APP_SECRET'])

    message = 'Sending sms to {} with text "{}"'.format(number, text)
    logger.info(message)

    try:
        response = client.send_message(number, text)
        print(response)
    except Exception as e:
        logging.error('Failed to send sms {} {} {}'.format(number, text, e))
