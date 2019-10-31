# ratechecker

The `ratechecker` app supports an API that exposes lookups of interest data given a set of loan criteria.

## Getting started

To explore the API, first load the sample data:

```sh
$ ./manage.py load_daily_data ratechecker/data/sample.zip
```

To access the root API endpoint, visit:

http://127.0.0.1:8000/oah-api/rates/rate-checker

After loading the sample dataset, you should be able to see some sample results. An example query with available rate data is:

http://127.0.0.1:8000/oah-api/rates/rate-checker?loan_type=CONF&loan_term=30&minfico=640&maxfico=640&rate_structure=FIXED&state=AK&loan_amount=150000&ltv=95&lock=30

An example query with no results is:

http://127.0.0.1:8000/oah-api/rates/rate-checker?loan_type=CONF&loan_term=30&minfico=640&maxfico=640&rate_structure=FIXED&state=AK&loan_amount=150000&ltv=95&lock=60

## Loading data

Interest rate data is stored in database tables accessed via the Django models defined in `ratechecker.models`. Data can be loaded using the `load_daily_data` management command:

```sh
$ ./manage.py load_daily_data dataset.zip
```

Loaded data can be validated using an set of predetermined scenarios:

```sh
$ ./manage.py load_daily_data --validation-scenario-file scenarios.jsonl dataset.zip 
```

Optionally, existing data can be revalidated without reloading:


```sh
$ ./manage.py load_daily_data --validation-scenario-file scenarios.jsonl --validate-only dataset.zip 
```

See below for more information on scenario validation.

### Dataset format

The provided dataset file must be in ZIP format and contain the following files at its root level:

- `CoverSheet.xml`

  This is an XML file describing the dataset, matching this format:
  
  ```xml
  <?xml version="1.0" encoding="utf-8"?>
  <CFPB xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <ProcessDate>
      <Date>20170130</Date>
    </ProcessDate>
    <Scenarios>
      <Scenario>
        <ScenarioNo>1</ScenarioNo>
        <AdjustedRates>3.250</AdjustedRates>
        <AdjustedPoints>0.000</AdjustedPoints>
      </Scenario>
      <Scenario>
        <ScenarioNo>2</ScenarioNo>
        <AdjustedRates/>
        <AdjustedPoints/>
    </Scenarios>
  </CFPB>
  ```
  
  The `ProcessDate/Date` element should contain the date of the data being loaded in `YYYYMMDD` format. The `Scenarios` key element contain a list of expected scenario results to be used to validate the dataset. Each `Scenario` sub-element must contain a numeric ID and, if expected, an interest rate/point combination for that scenario.
  
- `20170130_region.txt`

  (The date in this filename and all other filenames must match the date provided in the XML cover sheet.)  

  This is a CSV file containing a list of geographic regions and the states they are associated with. See `ratechecker.loader.RegionLoader` for format details.
  
- `20170130_product.txt`

  This is a CSV file containing rate product data, including lender name and criteria such as loan-to-value and FICO score requirements. See `ratechecker.loader.ProductLoader` for format details.
  
- `20170130_rate.txt`

  This is a CSV file containing the actual rate data for each product, including geographic region, lock term, and base rate and points. See `ratechecker.loader.RateLoader` for format details.
  
- `20170130_adjustment.txt`

  This is a CSV file containing rate adjustment data. See `ratechecker.loader.AdjustmentLoader` for format details.
  
- `20170130_fee.txt`

  This is a CSV file containing rate fee data. See `ratechecker.loader.FeeLoader` for details.

See the provided `data/sample.zip` file for an example minimal dataset.

## Validation

Loaded data can be validated against a set of predetermined scenarios that check the expected behavior of the rate search algorithm. The `CoverSheet.xml` file in the loaded dataset contains the expected API results; a [JSONL format](http://jsonlines.org/) file provided to the loader command contains the scenario definitions that should produce those results.

Each line in the scenario file (for example `ratechecker/data/sample-scenarios.jsonl`) contains the set of API parameters that define a single interest rate search, for example:

```
{"scenario_id": 1, "institution": "FOOBAR", "state": "AK", "loan_purpose": "PURCH", "loan_term": 30, "rate_structure": "FIXED", "loan_type": "CONF", "loan_amount": 150000, "ltv": 95, "minfico": 640, "maxfico": 640, "lock": 30}
```

The corresponding section of the dataset cover sheet XML looks like this:

```xml
<Scenarios>
  <Scenario>
    <ScenarioNo>1</ScenarioNo>
    <AdjustedRates>4.375</AdjustedRates>
    <AdjustedPoints>0.500</AdjustedPoints>
  </Scenario>
</Scenarios>
```

This scenario tests that a query to the API for a fixed rate loan in the amount of $150,000 in Alaska, etc. will return at least one rate at 4.375% with 0.5 points.

Unfortunately, full interest rate data and test scenarios cannot be made public as part of this repository.
