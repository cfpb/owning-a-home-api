from ratechecker.views import RateCheckerStatus, rate_checker


try:
    from django.urls import re_path
except ImportError:
    from django.conf.urls import url as re_path


urlpatterns = [
    re_path(r"rate-checker$", rate_checker, name="rate-checker"),
    re_path(
        r"rate-checker/status$",
        RateCheckerStatus.as_view(),
        name="rate-checker-status",
    ),
]
