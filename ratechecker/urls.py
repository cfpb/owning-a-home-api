from django.conf.urls import url

from ratechecker.views import (
    RateCheckerStatus, rate_checker, rate_checker_fees
)


urlpatterns = [
    url(r'rate-checker$',
        rate_checker, name='rate-checker'),
    url(r'rate-checker/status$',
        RateCheckerStatus.as_view(), name='rate-checker-status'),
    url(r'rate-checker-fees$',
        rate_checker_fees, name='rate-checker-fees'),
]
