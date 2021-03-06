"""
Django settings for jaqpot_ui project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
import base64
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's4&d(x$fcu$24qrac!&jv%4)c5hyz+)at%e32(b28ot_(lu!0^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'endless_pagination',
    'captcha',
    'jaqpot_ui',
    'haystack',
    'elasticsearch',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'jaqpot_ui.urls'

WSGI_APPLICATION = 'jaqpot_ui.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    'jaqpot_ui/static',
)

# Authentication settings
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
SITE_ID = 1
LOGIN_REDIRECT_URL = '/'

TEMPLATE_DIRS = (
  'jaqpot_ui/templates',
)


# External Authenticator
EXT_AUTH_URL_LOGIN = 'https://opensso.in-silico.ch:443/auth/authenticate?uri=service=openldap'
EXT_AUTH_URL_LOGOUT = 'http://opensso.in-silico.ch/opensso/identity/logout'

#URL_1 = 'http://enanomapper.ntua.gr:8880/jaqpot/services'
SERVER_URL = os.getenv('JAQPOT_BASE_SERVICE', 'http://localhost:8080/jaqpot/services')


TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.request',
)

ENDLESS_PAGINATION_PREVIOUS_LABEL = 'Previous'
ENDLESS_PAGINATION_NEXT_LABEL = 'Next'
ENDLESS_PAGINATION_PER_PAGE = 10

#EMAIL_HOST = 'localhost'
#EMAIL_PORT = 25
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'eanagnosto@gmail.com'
EMAIL_HOST_PASSWORD = base64.b64decode('ZXZhbmdlbGlhOTA=')


SOUTH_MIGRATION_MODULES = {
    'captcha': 'captcha.south_migrations',
}

TEMPLATE_LOADERS = (
    #'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.app_directories.Loader',
)

#Elastic Search
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django.request':{
            'handlers': ['console'],
            'propagate': False,
            'level': 'DEBUG',
        },
    },
}
