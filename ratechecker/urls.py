from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'rate-checker$', 'ratechecker.views.rate_checker', name='rate-checker'),
    url(r'rate-checker-fees$', 'ratechecker.views.rate_checker_fees', name='rate-checker-fees'),
)
