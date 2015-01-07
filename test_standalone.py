# Shamelessly borrowed from
# http://stackoverflow.com/questions/3841725/how-to-launch-tests-for-django-reusable-app/3851333#3851333
import os
import sys
from django.conf import settings

DIRNAME = os.path.dirname(__file__)
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE':
            'django.db.backends.sqlite3',
        },
    },
    USE_TZ=True,
    ROOT_URLCONF='oahapi.oahapi.urls',
    INSTALLED_APPS=('ratechecker',
                    'countylimits')
)


from django.test.simple import DjangoTestSuiteRunner
test_runner = DjangoTestSuiteRunner(verbosity=1)
failures = test_runner.run_tests(['ratechecker', 'countylimits', ], verbosity=1)
if failures:
    sys.exit(failures)
