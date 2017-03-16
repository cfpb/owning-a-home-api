All notable changes to this project will be documented in this file.
We follow the [Semantic Versioning 2.0.0](http://semver.org/) format.

## Unreleased
- Add new ratechecker API endpoint to check data load timestamp.

## 0.9.94 - 2017-02-02
- Add a monitor to watch for changes in census county values
- Adds automated county mortgage limit collection script and command
- Loses the "v" in the release number

## 0.9.93 - 2017-01-25
- Remove unused `mortgageinsurance` app.
- Add a monitor to watch for census county changes.
- `load_daily_data` optional `--database` argument.
- Bring ratechecker data load job code up to date.

## 0.9.92 - 2016-12-31
- 2017 update for county-level mortgage-limit data 

## 0.9.91 - 2016-12-02
- API security update for error responses

## 0.9.9 - 2016-10-27
- Updated djangorestframework from 2.4.3 to 3.1.3
- Bumped Django requirements to 1.8.15 to match cfgov site
- Added a whitelist check for the countylimit API's `state` querystring parameter

## 0.9.6 - 2015-01-09
- continue loading data even if some scenarios do not match

## 0.9.5 - 2015-01-07
- add 2015 county limits data file
- fix Travis CI testing

## 0.9.3 - 2015-01-07
- stop ignoring scenarios with FHA-HB loans during data load

## 0.9.2 - 2015-01-06
- use .5 limit in both API results and testing of data loads

## 0.9.1 - 2015-01-05
- alpha version of the tool


## 0.0.1 - 2014-11-07

### Added
- Initial state.
