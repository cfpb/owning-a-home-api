from django.conf.urls import url
from countylimits.views import county_limits

urlpatterns = [
    url(r'^$', county_limits, name='county_limits'),
]
