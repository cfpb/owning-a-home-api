from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    # Examples:
    # url(r'^$', 'oahapi.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^rates/', include('ratechecker.urls', namespace='ratechecker')),
    url(r'^county/', include('countylimits.urls', namespace='countylimits'))
)
