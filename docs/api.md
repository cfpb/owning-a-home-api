# API endpoints

The Owning-a-home API includes three modules:

#### ratechecker
This app exposes two API endpoints, `/oah-api/rates/rate-checker` and
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

#### countylimits
This app exposes a single API endpoint, `/oah-api/county`, which requires a `state` parameter for querying Federal Housing Administration loan lending limit, Government-Sponsored Enterprises mortgage loan limit and the Department of Veterans Affairs loan guaranty program limit for the counties in a given state.

| Param name | Description | Required | Default value | Acceptable values |
| ---------- | ----------- |:--------:| -------------:| -----------------:|
| state | The US state | Yes | N/A | _all the US state's abbreviations_ or _fips codes_ |

countylimits will return a JSON object containing `state`, `county`, `complete_fips`, `gse_limit`, `fha_limit`, and `va_limit`.

countylimits has a management command, `load_county_limits`, which loads these limits from a CSV file. Source CSVs are stored in the /data directory. The latest version is [data/2017/2017_amended.csv](https://github.com/cfpb/owning-a-home-api/blob/master/data/2017/2017_amended.csv).

The `load_county_limits` command takes two arguments to fully run: file path and `--confirm=y`

So the full command to load the data for 2017 would be:

```
python manage.py load_county_limits data/2017/2017_amended.csv --confirm=y
```

See `/data/2017/README.md` for details about the 2017 data.

#### mortgageinsurance
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
