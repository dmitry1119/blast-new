"""
Django settings for blast project.

Generated by 'django-admin startproject' using Django 1.9.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'om7$m&moqi+r5c5s&(*vonrx7cc!1ulluo%lod!f9fq0s+1z1p'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'push_notifications',
    'core',
    'smsconfirmation',
    'posts',
    'tags',
    'countries',
    'users',
    'notifications'
]

AUTHENTICATION_BACKENDS = [
    'users.backends.UsernameCaseInsensitiveBackend'
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'blast.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'blast.wsgi.application'

SWAGGER_SETTINGS = {
    'exclude_namespaces': [],
    'api_version': '1',
    'api_path': '/',
    'enabled_methods': [
        'get',
        'post',
        'patch',
        'delete'
    ],
    'api_key': '',
    'is_authenticated': False,
    'is_superuser': False,
    'unauthenticated_user': 'django.contrib.auth.models.AnonymousUser',
    'permission_denied_handler': None,
    'resource_access_handler': None,
    'info': {
        'contact': 'vlmihnevich@gmail.com',
        'description': 'This is swagger documentation for blast API',
        'license': 'Apache 2.0',
        'title': 'Blast Api',
    },
    'doc_expansion': 'none',
}


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',  # TODO(VM): Get rid?
        'rest_framework.authentication.SessionAuthentication',  # TODO(VM): Get rid?
        'rest_framework.authentication.TokenAuthentication',
    ),

    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardResultsSetPagination'
}

SINCH = {
    'APP_KEY': '155edefb-991d-4e14-864e-4e9451a21bd6',
    'APP_SECRET': '2JS8PKvSyk2AgNf+3DIvZQ==',
}

CELERYBEAT_SCHEDULE = {
    'clear-expired-posts': {
        'task': 'posts.tasks.clear_expired_posts',
        'schedule': timedelta(minutes=5),
    },
    'send-notifications': {
        'task': 'posts.tasks.send_expire_notifications',
        'schedule': timedelta(minutes=3)
    }
}

# CELERY SETTINGS
BROKER_URL = 'redis://localhost:6379/1'
CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


PUSH_NOTIFICATIONS_SETTINGS = {
    'APNS_CERTIFICATE': os.path.join(PARENT_DIR, 'sertificates/apsBlastProd.pem'),
}

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PARENT_DIR, 'static/')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(PARENT_DIR, 'media/')

AUTH_USER_MODEL = 'users.User'

ADMINS = [('vlmihnevich', 'vlmihnevich@gmail.com')]

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'djangomailservice@gmail.com'
EMAIL_HOST_PASSWORD = 'w_sp[q12uQmZ36cjQ'

# import logging
# logger = logging.getLogger(__name__)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        }
    },
    'formatters': {
        'main_formatter': {
            'format': '%(levelname)s:%(name)s: %(message)s '
                      '(%(asctime)s; %(filename)s:%(lineno)d)',
            'datefmt': "%Y-%m-%d %H:%M:%S",
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'main_formatter',
        },
        'production_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/main.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 7,
            'formatter': 'main_formatter',
            'filters': ['require_debug_false'],
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/debug_main.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 7,
            'formatter': 'main_formatter',
            'filters': ['require_debug_true'],
        },
    },
    'loggers': {
        'core.decorators': {
            'handlers': ['console'],
        },
        '': {
            'handlers': ['console', 'production_file', 'debug_file'],
            'level': 'DEBUG',
        },
    },
}