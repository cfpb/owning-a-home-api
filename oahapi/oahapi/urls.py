from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(r'^oah-api/rates/', include('ratechecker.urls')),
    url(r'^oah-api/county/$', include('countylimits.urls')),
    url(r'^oah-api/mortgage-insurance/$', include('mortgageinsurance.urls')),
)
