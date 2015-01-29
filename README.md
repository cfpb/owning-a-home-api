# Owning a Home API [![Build Status](https://travis-ci.org/cfpb/owning-a-home-api.svg?branch=master)](https://travis-ci.org/cfpb/owning-a-home-api)

This provides an API for the [Owning a Home project](https://github.com/cfpb/owning-a-home). The tool will return rates available on the market. 
Note that it relies on bringing data from an external (not free) source.

**Status**

The API is at version 1.0, a work in progress. 

**Dependencies**
 * [Django 1.6](https://docs.djangoproject.com/en/1.6/)
 * [Django Rest Framework](http://www.django-rest-framework.org)
 * [Django localflavor](https://github.com/django/django-localflavor)
 * [MySQL Python](http://mysql-python.sourceforge.net/)
 * [South](http://south.aeracode.org)
 * [django-cors-headers](https://github.com/ottoyiu/django-cors-headers)

## Installing and using

The tool is a Django module and can be installed and run inside your Django project.
Here's help for setting up a Django project and adding modules:
 - [Starting a project](https://docs.djangoproject.com/en/1.6/intro/tutorial01/)
 - [Adding modules](https://docs.djangoproject.com/en/1.6/ref/django-admin/#startproject-projectname-destination)

Install the app (ideally in a virtual environment):

```shell
git clone https://github.com/cfpb/owning-a-home-api
cd owning-a-home-api && pip install -e .
```

In your core Django application, add `ratechecker` to the INSTALLED_APPS.  For example
```python
INSTALLED_APPS += (
    'rest_framework',
    'countylimits',
    'ratechecker',
    'south',
)
```

Also add the following urls to your core Django application’s urls.py:
```python
    url(r'^oah-api/rates/', include('ratechecker.urls')),
    url(r'^oah-api/county/', include('countylimits.urls')),
```

##What the app does

Owning a Home API includes two Django apps:

###ratechecker
This app exposes a single API endpoint, `/oah-api/rates/rate-checker`, with the following parameters:
 - lock
 - points
 - property_type
 - loan_purposes
 - io
 - institution
 - loan_amount
 - price
 - state
 - loan_type
 - maxfico
 - minfico
 - rate_structure
 - loan_term
 - arm_type
 - ltv

ratechecker will return a JSON object containing `data` and `timestamp`

ratechecker has a management command, `load_daily_data`, which loads daily interest rate data from CSV.

###countylimits
This app exposes a single API endpoint, `/oah-api/county`, which requires a `state` parameter for querying Federal Housing Administration loan lending limit, Government-Sponsored Enterprises mortgage loan limit and the Department of Veterans Affairs loan guaranty program limit for the counties in a given state.

countylimits will return a JSON object containing `state`, `county`, `complete_fips`, `gse_limit`, `fha_limit`, and `va_limit`.

countylimits has a management command, `load_county_limits`, which loads these limits from a CSV file which is provided in [`data/county_limit_data-flat.csv`](https://github.com/cfpb/owning-a-home-api/blob/master/data/county_limit_data-flat.csv)

## Testing
Testing requires mock, so use `pip install mock` before running tests with `python test_standalone.py`
















```shell
git clone https://github.com/cfpb/owning-a-home-api
cd owning-a-home-api && pip install -e .
```







To test run ``./manage.py test [ratechecker]``

## Contributions

We welcome contributions with the understanding that you are contributing to a project that is in the public domain, and anything you contribute to this project will also be released into the public domain. See our CONTRIBUTING file for more details.
