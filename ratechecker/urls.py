from django.conf.urls import url

from ratechecker.views import (
    RateCheckerStatus, rate_checker
)


urlpatterns = [
    url(r'rate-checker$',
        rate_checker, name='rate-checker'),
    url(r'rate-checker/status$',
        RateCheckerStatus.as_view(), name='rate-checker-status'),
]
