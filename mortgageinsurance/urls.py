from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'$', 'mortgageinsurance.views.mortgage_insurance', name='mortgage_insurance'),
)
