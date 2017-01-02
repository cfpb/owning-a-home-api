from django.conf.urls import include, url

urlpatterns = [
    url(r'^oah-api/rates/', include('ratechecker.urls')),
    url(r'^oah-api/county/$', include('countylimits.urls')),
]
