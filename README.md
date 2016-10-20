[![Build # Status](https://travis-ci.org/cfpb/owning-a-home-api.svg?branch=master)](https://travis-ci.org/cfpb/owning-a-home-api) [![Coverage Status](https://coveralls.io/repos/cfpb/owning-a-home-api/badge.svg?branch=master)](https://coveralls.io/r/cfpb/owning-a-home-api?branch=master)

# Owning a Home API 

This project feeds detailed mortgage market data to the Consumer Finance Protection Bureau's [Owning a Home suite of tools](http://www.consumerfinance.gov/owning-a-home/). Unfortunately, the raw data set it serves is not available publicly and is not in this repository. 

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

The API can be run and explored as is, but it was built to be a service for the [Owning-a-home tools at consumerfinance.gov](http://www.consumerfinance.gov/owning-a-home/)

You can install the API and its sister project, https://github.com/cfpb/owning-a-home, insdie the public project that powers consumerfinance.gov -- https://github.com/cfpb/cfgov-refresh

The cfgov-refresh [documentation](https://cfpb.github.io/cfgov-refresh/) describes how to install sub-modules such as the owning-a-home API inside cfgov-refresh.

#### Data
This repo only contains limited data, but deeper information about mortgage interest rates and mortgage insurance can be found at consumerfinance.gov's [Interest-rate checker tool](http://www.consumerfinance.gov/owning-a-home/explore-rates/).

## Exploring the app

Owning a Home API includes three modules:

####ratechecker
This app exposes a single API endpoint, `/oah-api/rates/rate-checker` and
`/oah-api/rates/rate-checker-fees`, with the following parameters:

| Param name | Description | Required | Default value | Acceptable values<br>(values = description) |
| ---------- | ----------- |:--------:| -------------:| :-----------------|
| arm_type | The type of ARM | No, unless rate_structure=arm | N/A | 3-1 = 3/1 ARM,<br>5-1 = 5/1 ARM,<br>7-1 = 7/1 ARM,<br>10-1 = 10/1 ARM |
| institution | The institution name | No | N/A | _any valid institution name_, for ex. BANKA, BANKB, etc.|
| io | Interest only flag -- only applicable to ARM loans | No | 0 | 0 = false,<br>1 = true,<br>blank |
| loan_amount | The amount of the loan | Yes | N/A | _any positive integer_ |
| loan_purpose | The purpose of the loan | No | PURCH | PURCH = New Purchase,<br>REFI = Refinance |
| loan_term | The loan term (years) | Yes | N/A | 30, 15 |
| loan_type | The type of loan | Yes | N/A | JUMBO = Jumbo Loan,<br>CONF = Conventional Loan,<br>AGENCY = Agency Loan,<br>FHA = Federal Housing Administration Loan,<br>VA = Veteran Affairs Loan,<br>VA-HB = Veteran Affairs High Balance Loan,<br>FHA-HB = Federal Housing Administration High Balance Loan |
| lock | Rate lock period | No | 60 | Typically, 30, 45, or 60.<br>One lender in the database has non-standard rate lock periods, so the code converts a single number to a range: <= 30; >30 and <=45; >45 and <= 60 respectively |
| ltv [*1](#1) | Loan to value | No | N/A | Calculated by dividing the loan amount by the house price |
| maxfico | The maximum FICO score | Yes | N/A | 0 - 850.<br>In practice, <600 will return no results.  For optimal functioning, MinFICO and MaxFICO should be coordinated.  Either, they should be the same value, thereby providing a point estimate of the FICO score, or they should be configured to provide a 20-point range, eg, 700-719.  Ranges should be specified to start on an even 20 multiple and end on a 19, 39, 59, etc., except for the top bucket which is 840-850. |
| minfico | The minimum FICO score | Yes | N/A | 0 - 850,<br>see maxfico for more info. |
| points | Points | No | 0 | This number is used as the centroid of a range, +/- 0.5, to constrain the results. Input could be any decimal roughly within -4 to +4, but in practice anything outside of -2 to +3 is likely to have few results. |
| price | The price of the property | Yes | N/A | _In general, should be larger than the loan_amount._ |
| property_type | The property type | No | SF | SF = Single Family;<br>CONDO = Condominium;<br>COOP = Housing Cooperative (co-op) |
| rate_structure | The rate structure of the loan | Yes | N/A | FIXED = Fixed Rate,<br>ARM = Adjusted Rate Mortgage |
| state | The US state | Yes | N/A | _all the US state's abbreviations_ |

*1: We actually calculate its value and don't check the value sent in request

ratechecker will return a JSON object containing `data` and `timestamp`, it will also contain
`fees` field when requesting `/oah-api/rates/rate-checker-fees`.

ratechecker has a management command, `load_daily_data`, which loads daily interest rate data from CSV.

####countylimits
This app exposes a single API endpoint, `/oah-api/county`, which requires a `state` parameter for querying Federal Housing Administration loan lending limit, Government-Sponsored Enterprises mortgage loan limit and the Department of Veterans Affairs loan guaranty program limit for the counties in a given state.

| Param name | Description | Required | Default value | Acceptable values |
| ---------- | ----------- |:--------:| -------------:| -----------------:|
| state | The US state | Yes | N/A | _all the US state's abbreviations_ or _fips codes_ |

countylimits will return a JSON object containing `state`, `county`, `complete_fips`, `gse_limit`, `fha_limit`, and `va_limit`.

countylimits has a management command, `load_county_limits`, which loads these limits from a CSV file provided in [`data/county_limit_data-flat.csv`](https://github.com/cfpb/owning-a-home-api/blob/master/data/county_limit_data-flat.csv)

####mortgageinsurance
This app exposes a single API endpoint, `/oah-api/mortgage-insurance`, with the following parameters:

| Param name | Description | Required | Default value | Acceptable values<br>(values = description) |
| ---------- | ----------- |:--------:| -------------:| :-----------------|
| arm_type | The type of ARM | No, unless rate_structure=arm | N/A | 3-1 = 3/1 ARM,<br>5-1 = 5/1 ARM,<br>7-1 = 7/1 ARM,<br>10-1 = 10/1 ARM |
| loan_amount | The amount of the loan | Yes | N/A | _any positive integer_ |
| loan_term | The loan term (years) | Yes | N/A | 30, 15 |
| loan_type | The type of loan | Yes | N/A | JUMBO = Jumbo Loan,<br>CONF = Conventional Loan,<br>AGENCY = Agency Loan,<br>FHA = Federal Housing Administration Loan,<br>VA = Veteran Affairs Loan,<br>VA-HB = Veteran Affairs High Balance Loan,<br>FHA-HB = Federal Housing Administration High Balance Loan |
| maxfico | The maximum FICO score | Yes | N/A | 0 - 850.<br>In practice, <600 will return no results.  For optimal functioning, MinFICO and MaxFICO should be coordinated.  Either, they should be the same value, thereby providing a point estimate of the FICO score, or they should be configured to provide a 20-point range, eg, 700-719.  Ranges should be specified to start on an even 20 multiple and end on a 19, 39, 59, etc., except for the top bucket which is 840-850. |
| minfico | The minimum FICO score | Yes | N/A | 0 - 850,<br>see maxfico for more info. |
| price | The price of the property | Yes | N/A | _In general, should be larger than the loan_amount._ |
| rate_structure | The rate structure of the loan | Yes | N/A | FIXED = Fixed Rate,<br>ARM = Adjusted Rate Mortgage |
| va_status | The Veteran Status | No, unless loan_type=va or va-hb | N/A | DISABLED = Veteran with Disablility<br>RES-NG = Reserve or National Guard<br>REGULAR = Regular |
| va_first_use | Is this the first time using VA loan? | No, unless loan_type=va or va-hb | N/A | 1 = True<br>0 = False |

mortgageinsurance will return a JSON object containing `data` and `request`.  Data will contain `monthly` for monthly average premium in percentages (it is an average premium calculated based on premium from all insurers), and `upfront` for upfront premium in percentage.  No data will be returned if no premium were found.  `Request` will be the parameter list.

mortgageinsurance has a management command, `load_mortgage_insurance`, which loads monthly and upfront data from two CSV files.

## Testing
You can run Python unit tests and see code coverage by running:
```
./pytest.sh
```

#### If using MySQL
For testing, the default Django sqlite database will be set up for you automatically. If you want to load a MySQL dataset, you can edit `settings_for_testing.py` to uncomment the MySQL database section and install MySQL as follows:
```shell
brew install mysql
```
Start the MySQL Server, this command may need to be run again (if stopped) when trying to bring up the web server later:
```shell
mysql.server start
```
Set Password for root:
```shell
mysql_secure_installation
```
Connect to MySQL with root and password:
```shell
mysql -uroot -p
```
Then create an owning-a-home database:
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

If you have access to mortgage data, you could load it like so:

```
mysql -uroot -p oah < [PATH TO YOUR .sql FILE]
```


## Contributions

We welcome contributions with the understanding that you are contributing to a project that is in the public domain, and anything you contribute to this project will also be released into the public domain. See our CONTRIBUTING file for more details.
