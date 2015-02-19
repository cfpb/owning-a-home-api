# Owning a Home API [![Build Status](https://travis-ci.org/cfpb/owning-a-home-api.svg?branch=master)](https://travis-ci.org/cfpb/owning-a-home-api)

This provides an API for the [Owning a Home project](https://github.com/cfpb/owning-a-home). The tool will return rates available on the market.
Note that it relies on bringing data from an external (not free) source.

**Status**

The API is at version 0.9.6, a work in progress.

**Dependencies**
 * [Python 2.6](https://www.python.org/download/releases/2.6/)
 * [virtualenv](https://virtualenv.pypa.io/en/latest/)
 * [Django 1.6](https://docs.djangoproject.com/en/1.6/)
 * [Django Rest Framework](http://www.django-rest-framework.org)
 * [Django localflavor](https://github.com/django/django-localflavor)
 * [MySQL Python](http://mysql-python.sourceforge.net/)
 * [South](http://south.aeracode.org)
 * [django-cors-headers](https://github.com/ottoyiu/django-cors-headers)
 * [MySQL](http://www.mysql.com)
 * [Homebrew](http://brew.sh)
 * [pip](https://pypi.python.org/pypi/pip)

## Installing and using it locally

The tool is a Django module and can be installed and run inside a Django project.

These instructons assume that you are using a Mac with OS X Yosemite and with [Homebrew](http://brew.sh) installed:

###Install required components

####MySQL
**Install MySQL if you do not have it
```shell
brew install mysql
```
Start the MySQL Server, this command may need to be run again (if stopped) when trying to bring up the web server later
```shell
mysql.server start
```
Set Password for root
```shell
mysql_secure_installation
```
Connect to MySQL with root and password
```shell
mysql -uroot -p
```
Then create an owning-a-home database
```shell
create database oah;
```
If you would like to connect with a different user other than root, you can create a user, and replace `oah_user` with your desired username and `password` with your desired password:
```shell
create user 'oah_user'@'localhost' identified by 'password';
grant all privileges on oah.* to 'oah_user'@'localhost';
flush privileges;
exit
```
You can now connect to MySQL with your newly created username and password and have access to `oah`:
```shell
mysql -u oah_user -p
# enter your password
show databases;
use oah;
exit
```

It is recommended that you use a [virtualenv](https://virtualenv.pypa.io/en/latest/) to keep your dependencies organized.
```shell
mkvirtualenv oah
```
Create a folder for your project in a workspace or other location(`~/workspace` in this case):
```shell
cd ~/workspace
mkdir oah_api && cd oah_api
pip install django==1.6
# Create a sample app
django-admin.py startproject oah_app
```

Edit oah_app\settings.py to use MySQL as the database, edit the `DATABASES` to the following, and replace the database user name and password (or root if you did not create one) you created above:
```python
DATABASES = {
    'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'oah',
           'USER': 'oah_user',
           'PASSWORD': 'password',
   }
}
```
Install mysql-python module
```shell
pip install mysql-python
```

Sync the database and make sure it can be run and accessible in a browser (http://127.0.0.1:8000) (you may get an error if your MySQL Server is not running, if that's the case, run `mysql.server start` and try the following again:
```shell
python manage.py syncdb
python manage.py runserver
```
Now you are ready to install the app:

Go back to your workspace (`~\workspace` in the case above) or the location you installed `oah_api`, please do not clone inside `oah_api` folder:
```shell
cd ~\workspace
```

Clone and install requirements from the app in virtualenv `oah` created above:
```shell
git clone https://github.com/cfpb/owning-a-home-api
pip install -e owning-a-home-api
cd owning-a-home-api && pip install -r requirements.txt
```
Back to Django project you created earlier:
```shell
cd ~/workspace/oah_api
```

Add the apps from `owning-a-home-api` to your Django project you created earlier in `INSTALLED_APPS` from `oah_api/settings.py`:
```python
INSTALLED_APPS += (
    ...
    'rest_framework',
    'countylimits',
    'ratechecker',
    'south',
)
```

Also add the following urls to your core Django project `oah_api/urls.py`:
```python
    url(r'^oah-api/rates/', include('ratechecker.urls')),
    url(r'^oah-api/county/', include('countylimits.urls')),
```

Sync and migrate the Database:
```shell
python manage.py syncdb
python manage.py migrate
```

You can now start the app again to make sure it is accessible in a browser (http://127.0.0.1:8000):
```shell
python manage.py runserver
```

Loading the data:
We only supply county limits data as those are open to the public, we do not supply rate checker data.

Loading county limits data:
```shell
python manage.py load_county_limits ~/workspace/owning-a-home-api/data/county_limit_data-flat.csv --confirm=y
```

##What the app does

Owning a Home API includes two Django apps:

####ratechecker
This app exposes a single API endpoint, `/oah-api/rates/rate-checker`, with the following parameters:

| Param name | Required | Default value | Acceptable values |
| ---------- |:--------:| -------------:| -----------------:|
| arm_type | No, unless rate_structure=arm | N/A | 3-1, 5-1, 7-1, 10-1 |
| institution | No | N/A | _any valid institution name_, for ex. PNC, WELLS, UNBK, etc.|
| io | No | 0 | |
| loan_amount | Yes | N/A | _any positive integer_ |
| loan_purpose | No | PURCH | PURCH, REFI |
| loan_term | Yes | N/A | 30, 15 |
| loan_type | Yes | N/A | JUMBO, CONF, AGENCY, FHA, VA, VA-HB, FHA-HB |
| lock | No | 60 | |
| ltv [*1](#1) | No | N/A | |
| maxfico | Yes | N/A | 0 -> 850 |
| minfico | Yes | N/A | 0 -> 850 |
| points | No | 0 | |
| price | Yes | N/A | _better be larger than loan_amount_ |
| property_type | No | SF | |
| rate_structure | Yes | N/A | FIXED, ARM |
| state | Yes | N/A | _all the US state's abbreviations_ |

*1: We actually calculate its value and don't check the value sent in request

ratechecker will return a JSON object containing `data` and `timestamp`

ratechecker has a management command, `load_daily_data`, which loads daily interest rate data from CSV.

####countylimits
This app exposes a single API endpoint, `/oah-api/county`, which requires a `state` parameter for querying Federal Housing Administration loan lending limit, Government-Sponsored Enterprises mortgage loan limit and the Department of Veterans Affairs loan guaranty program limit for the counties in a given state.

| Param name | Required | Default value | Acceptable values |
| ---------- |:--------:| -------------:| -----------------:|
| state | Yes | N/A | _all the US state's abbreviations_ or _fips codes_ |

countylimits will return a JSON object containing `state`, `county`, `complete_fips`, `gse_limit`, `fha_limit`, and `va_limit`.

countylimits has a management command, `load_county_limits`, which loads these limits from a CSV file provided in [`data/county_limit_data-flat.csv`](https://github.com/cfpb/owning-a-home-api/blob/master/data/county_limit_data-flat.csv)

## Testing
Testing requires mock, so you'll need to install that before running tests.


```shell
pip install mock
./manage.py test [ratechecker]
```

## Contributions

We welcome contributions with the understanding that you are contributing to a project that is in the public domain, and anything you contribute to this project will also be released into the public domain. See our CONTRIBUTING file for more details.
