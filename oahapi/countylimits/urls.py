from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'$', 'countylimits.views.county_limits', name='county_limits'),
)
