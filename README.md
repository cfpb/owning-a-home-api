[![Build # Status](https://travis-ci.org/cfpb/owning-a-home-api.svg?branch=master)](https://travis-ci.org/cfpb/owning-a-home-api) [![Coverage Status](https://coveralls.io/repos/cfpb/owning-a-home-api/badge.svg?branch=master)](https://coveralls.io/r/cfpb/owning-a-home-api?branch=master)

# Owning a Home API 

This project feeds detailed mortgage market data to the Consumer Financial Protection Bureau's [Owning a Home suite of tools](http://www.consumerfinance.gov/owning-a-home/). Unfortunately, the raw data set it uses is not available publicly and is not in this repository.

What is included is the API code and some basic geographical data. If you want to give it a spin, here's how:

## Installing it locally

The tool is intended to be a module that runs inside a Django project, but it can be tested as a stand-alone app.

These instructions are for installation on a Mac with OS X Yosemite (version 10.10.x), but they could be adapted for other environments.

**Dependencies**
* [Python 2.7](https://www.python.org/download/releases/2.7/)
* [pip](https://pypi.python.org/pypi/pip)
* [virtualenv](https://virtualenv.pypa.io/en/latest/)
* [Django 1.8.15](https://docs.djangoproject.com/en/1.8/)
* [Django Rest Framework 3.1.3](http://www.django-rest-framework.org)
* [Django localflavor](https://github.com/django/django-localflavor)
* [django-cors-headers](https://github.com/ottoyiu/django-cors-headers)

**Optional**
* [Homebrew](http://brew.sh)
* [MySQL](http://www.mysql.com)
* [MySQL Python](http://mysql-python.sourceforge.net/)

#### Steps for firing up Django
- It's useful to create a [virtualenv](https://virtualenv.pypa.io/en/latest/) virtual environment to keep Python dependencies sandboxed:

```shell
mkvirtualenv oah
```

- Create a folder for your Django project in a workspace or other location you like (`~/workspace` in this case), clone the project (or your fork of it) into your directory and install requirements:

```
cd ~/workspace
git clone https://github.com/cfpb/owning-a-home-api.git
cd owning-a-home-api/
setvirtualenvproject
pip install -r requirements/test.txt
```

- Initialize your database, load some basic data and launch a development server:

```shell
python manage.py migrate --noinput
python manage.py load_county_limits ~/workspace/owning-a-home-api/data/county_limit_data-flat.csv --confirm=y
python manage.py runserver
```

You should be able to view these API pages locally:
- http://127.0.0.1:8000/oah-api/county/
- http://127.0.0.1:8000/oah-api/county/?state=FL
- http://127.0.0.1:8000/oah-api/rates/rate-checker
- http://127.0.0.1:8000/oah-api/rates/rate-checker-fees
- http://127.0.0.1:8000/oah-api/mortgage-insurance/
- http://127.0.0.1:8000/oah-api/mortgage-insurance/?loan_type=FHA&maxfico=719&minfico=700&price=20000&state=FL&loan_amount=15000&rate_structure=FIXED&loan_term=10

#### Embedding the API module

You can install the API and its sister project, https://github.com/cfpb/owning-a-home, insdie the public project that powers consumerfinance.gov -- https://github.com/cfpb/cfgov-refresh

The cfgov-refresh [documentation](https://cfpb.github.io/cfgov-refresh/) describes how to install sub-modules such as the owning-a-home API inside cfgov-refresh.

#### Data
This repo contains limited data, but you can explore mortgage interest rates in detail at the CFPB's [Interest-rate checker tool](http://www.consumerfinance.gov/owning-a-home/explore-rates/).

## Deeper dive

You can find more about using the API endpoints and the optional use of a MySQL database in our [API documentation pages](https://cfpb.github.io/owning-a-home-api/).


## Testing
You can run Python unit tests and see code coverage by running:
```
./pytest.sh
```

## Contributions

We welcome contributions with the understanding that you are contributing to a project that is in the public domain, and anything you contribute to this project will also be released into the public domain. See our CONTRIBUTING file for more details.
