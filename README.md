![Build Status](https://github.com/cfpb/owning-a-home-api/workflows/test/badge.svg)[![Coverage Status](https://coveralls.io/repos/cfpb/owning-a-home-api/badge.svg?branch=master)](https://coveralls.io/r/cfpb/owning-a-home-api?branch=master)

# Owning a Home API

This project feeds detailed mortgage market data to the Consumer Financial Protection Bureau's [Owning a Home suite of tools](http://www.consumerfinance.gov/owning-a-home/). Unfortunately, the main data set it uses is not available publicly and is not in this repository.

What is included is the API code and some basic geographical data. If you want to give it a spin, here's how:

## Installing it locally

The tool is intended to be a module that runs inside a Django project, but it can be tested as a stand-alone app.

These instructions are for installation on a Mac with OS X Yosemite (version 10.10.x), but they could be adapted for other environments.

**Dependencies**
* [Python 3.8](https://www.python.org/)
* [pip](https://pypi.python.org/pypi/pip)
* [virtualenv](https://virtualenv.pypa.io/en/latest/)
* [Django](https://docs.djangoproject.com/en/stable/)
* [Django Rest Framework](http://www.django-rest-framework.org)
* [Django localflavor](https://github.com/django/django-localflavor)
* [django-cors-headers](https://github.com/ottoyiu/django-cors-headers)

**Optional**
* [Homebrew](http://brew.sh)

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
pip install -e '.[testing]'
```

- Initialize your database, load some basic data and launch a development server:

```shell
./manage.py migrate --noinput
./manage.py loaddata countylimits/fixtures/countylimit_data.json
./manage.py load_daily_data ratechecker/data/sample.zip
./manage.py runserver
```

You should be able to view these API pages locally:
- http://127.0.0.1:8000/oah-api/county/
- http://127.0.0.1:8000/oah-api/county/?state=FL
- http://127.0.0.1:8000/oah-api/rates/rate-checker

#### Embedding the API module

You can install the API and its sister project, https://github.com/cfpb/owning-a-home, inside the public project that powers consumerfinance.gov -- https://github.com/cfpb/cfgov-refresh

The cfgov-refresh [documentation](https://cfpb.github.io/cfgov-refresh/) describes how to install sub-modules such as the owning-a-home API inside cfgov-refresh.

#### Data
This repo contains limited data, but you can explore mortgage interest rates in detail at the CFPB's [Interest-rate checker tool](http://www.consumerfinance.gov/owning-a-home/explore-rates/).

## Deeper dive

You can find [additional documentation for the `ratechecker` app](ratechecker).


##  Running Tests

If you have [Tox](https://tox.readthedocs.io/en/latest/) installed (recommended),
you can run the specs for this project with the `tox` command.

If not, this command will run the specs on the python version your local
environment has installed: `./manage.py test`.

If you run the tests via Tox, it will automatically display spec coverage information.
To get test coverage information outside of Tox, install [Coverage.py](https://coverage.readthedocs.io/en/coverage-4.5.1a/)
and run these commands:

```
coverage erase
coverage run manage.py test
coverage report
```


## API Docs

[Documentation](https://cfpb.github.io/owning-a-home-api/) for this repository is rendered via GitHub pages. They can be edited in the `docs/` directory, but to view or deploy them, you'll need to install the dependencies listed in the `docs_extras` section of `setup.py`:

```
pip install -e '.[docs]'
```

You can then preview your changes locally by running `mkdocs serve` and then reviewing <http://127.0.0.1:8000/>

When your changes are ready, you can submit them as a normal pull request. After that, you can use this command to publish them:

```
mkdocs gh-deploy --clean
```

That pushes the necessary files to the `gh-pages` branch.

## Contributions

We welcome contributions with the understanding that you are contributing to a project that is in the public domain, and anything you contribute to this project will also be released into the public domain. See our CONTRIBUTING file for more details.
