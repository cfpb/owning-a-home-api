try:
    from django.urls import include, re_path
except ImportError:
    from django.conf.urls import include
    from django.conf.urls import url as re_path


urlpatterns = [
    re_path(r"^oah-api/rates/", include("ratechecker.urls")),
    re_path(r"^oah-api/county/", include("countylimits.urls")),
]
