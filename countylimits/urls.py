from countylimits.views import county_limits


try:
    from django.urls import re_path
except ImportError:
    from django.conf.urls import url as re_path


urlpatterns = [
    re_path(r"^$", county_limits, name="county_limits"),
]
