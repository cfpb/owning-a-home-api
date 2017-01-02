import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..')))

# FIXTURE_DIRS = (
#    '{}/countylimits/fixtures/'.format(BASE_DIR),
# )

CUSTOM_INSTALLED_APPS = (
    'ratechecker',
    'countylimits',
    'rest_framework',
)

ALWAYS_INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

ALWAYS_MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

SECRET_KEY = "django_tests_secret_key"
DEBUG = True
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = []
INSTALLED_APPS = ALWAYS_INSTALLED_APPS + CUSTOM_INSTALLED_APPS
MIDDLEWARE_CLASSES = ALWAYS_MIDDLEWARE_CLASSES
ROOT_URLCONF = 'oahapi.urls'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'oah',
    }
}

# '''if using MySQL and a cfgov-refresh production data load:'''

# DATABASES = {
#     'default': {
#            'ENGINE': 'django.db.backends.mysql',
#            'NAME': 'v1',
#            'USER': 'root',
#            'PASSWORD': '',
#     }
# }

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
