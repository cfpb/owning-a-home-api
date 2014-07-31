from django.conf.urls import patterns, url

urlpatterns = patterns( 
    '',
    url(r'fakes$', 'ratechecker.views.fake_list' ,name='fake')
)
