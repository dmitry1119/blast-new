from blast.settings import *

DEBUG = False

ALLOWED_HOSTS = ['*']

CELERYBEAT_SCHEDULE = {
    'clear-expired-posts': {
        'task': 'posts.tasks.clear_expired_posts',
        'schedule': timedelta(seconds=60*5),
    },
    'send-notifications': {
        'task': 'posts.tasks.send_expire_notifications',
        'schedule': timedelta(seconds=60*3)
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'blast',
        'USER': 'blastadmin',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '5432',
        'ATOMIC_REQUESTS': True
    }
}
