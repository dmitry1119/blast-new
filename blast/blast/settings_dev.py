from blast.settings import *

ALLOWED_HOSTS = ['*']

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
