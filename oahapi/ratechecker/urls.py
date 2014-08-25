from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'rate-checker$', 'ratechecker.views.rate_checker', name='rate-checker')
)
