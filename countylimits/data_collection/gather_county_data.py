import os
import pytz
from collections import OrderedDict
from csv import DictReader
from csv import writer as Writer

import requests

from django.utils import timezone


TZ = pytz.timezone("US/Eastern")
AWARE_NOW = timezone.now().astimezone(TZ)
ERROR_MSG = "Script failed to process all files."
API_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = "{}/data".format(API_DIR)
CSV_DIR = "{}/base_data".format(DATA_DIR)
CHUMS_FHA_URL = "https://apps.hud.gov/pub/chums/cy{}-forward-limits.txt"
CHUMS_GSE_URL = "https://apps.hud.gov/pub/chums/cy{}-gse-limits.txt"
CHUMS_SPACING = [
    ("msa-code", (0, 5)),
    ("metro-code", (5, 10)),
    ("metro-name", (10, 60)),
    ("program", (60, 65)),
    ("limit-type", (65, 66)),  # S or H, standard or high
    ("median-price", (66, 73)),
    ("limit-1-unit", (73, 80)),
    ("limit-2-units", (80, 87)),
    ("limit-3-units", (87, 94)),
    ("limit-4-units", (94, 101)),
    ("state", (101, 103)),
    ("county-fips", (103, 106)),
    ("state-name", (106, 132)),
    ("county-name", (132, 147)),
    ("county-transaction-date", (147, 155)),
    ("limit-transaction-date", (155, 163)),
    ("median-price-determining-limit", (163, 170)),
    ("year-for-median-determining-limit", (170, 175)),
]
CHUMS_MAP = OrderedDict(CHUMS_SPACING)
FINAL_FIELDNAMES = [
    "State",
    "State FIPS",
    "County FIPS",
    "Complete FIPS",
    "County Name",
    "GSE limit",
    "FHA limit",
    "VA limit",
]


def load_FIPS():
    with open(f"{CSV_DIR}/county_FIPS.csv", "r", newline="") as f:
        reader = DictReader(f)
        return [row for row in reader]


def translate_data(data_list, data_map):
    rows = []
    for line in data_list:
        rows.append(
            {
                key: line[
                    data_map[key][0] : data_map[key][1]  # noqa: E203
                ].strip()
                for key in data_map
            }
        )
    return rows


def download_datafile(url):
    response = requests.get(url, verify=False)
    if response.ok:
        return response.text
    else:
        return "Error:\n{} {}\n{}".format(
            response.status_code, response.reason, response.url
        )


def dump_to_csv(filepath, headings, data):
    with open(filepath, "w") as f:
        fieldnames = [key for key in headings]
        writer = Writer(f)
        writer.writerow(fieldnames)
        for row in data:
            writer.writerow([row[key] for key in headings])


def assemble_final_data(fha_data, gse_data):
    final_data = []
    county_data = load_FIPS()
    county_by_fips = {row["Complete FIPS"]: row for row in county_data}
    states = sorted(set(row["State"] for row in county_data))
    state_fips = {state: "" for state in states}
    for state in states:
        for row in county_data:
            if row["State"] == state:
                state_fips[state] = row["State ANSI"]
                continue
    for row in fha_data:
        if row["state"] and row["county-fips"]:
            FIPS = state_fips[row["state"]] + row["county-fips"]
            final_data.append(
                {
                    "State": row["state"],
                    "State FIPS": state_fips[row["state"]],
                    "County FIPS": row["county-fips"],
                    "Complete FIPS": FIPS,
                    "County Name": county_by_fips[FIPS]["County Name"],
                    "GSE limit": None,
                    "FHA limit": int(row["limit-1-unit"]),
                    "VA limit": None,
                }
            )
    gse_by_fips = {}
    for row in gse_data:
        if row["state"] and row["county-fips"]:
            FIPS = state_fips[row["state"]] + row["county-fips"]
            gse_by_fips[FIPS] = int(row["limit-1-unit"])
    for row in final_data:
        limit = gse_by_fips[row["Complete FIPS"]]
        row["GSE limit"] = limit
        row["VA limit"] = limit
    return final_data


def get_chums_data(year=None):
    """
    Downloads and processes mortgage data files for the next year.

    Normally, updates are run in December preceding the new data year,
    so the default year is current year + 1.
    If updates need to be run for the current year, or any other year,
    then pass in your desired 'year' value.

    Files are available manually
    at https://apps.hud.gov/pub/chums/file_layouts.html
    """
    year = year or AWARE_NOW.year + 1
    msg = ""
    try:
        fha = download_datafile(CHUMS_FHA_URL.format(year)).split("\r\n")
        if fha[0].startswith("Error"):
            msg += fha[0]
            raise ValueError(fha[0])
        fha_data = translate_data(fha, CHUMS_MAP)
        dump_to_csv(
            "{}/forward_limits_{}.csv".format(CSV_DIR, year),
            CHUMS_MAP.keys(),
            fha_data,
        )
        msg += "FHA limits saved to {}/forward_limits_{}.csv\n".format(
            CSV_DIR, year
        )
        gse = download_datafile(CHUMS_GSE_URL.format(year)).split("\r\n")
        if gse[0].startswith("Error"):  # pragma: no cover tested above
            msg += gse[0]
            raise ValueError(gse[0])
        gse_data = translate_data(gse, CHUMS_MAP)
        gse_file = "{}/gse_limits_{}.csv".format(CSV_DIR, year)
        dump_to_csv(gse_file, CHUMS_MAP.keys(), gse_data)
        msg += "GSE limits saved to {}\n".format(gse_file)
        final_data = assemble_final_data(fha_data, gse_data)
        yearly_file = "{}/county_limit_data_flat_{}.csv".format(CSV_DIR, year)
        final_file = "{}/county_limit_data_latest.csv".format(DATA_DIR)
        dump_to_csv(yearly_file, FINAL_FIELDNAMES, final_data)
        dump_to_csv(final_file, FINAL_FIELDNAMES, final_data)
        msg += "Final flat file saved to {}\n".format(final_file)
        msg += (
            "All county source files processed.\n"
            "Data can be loaded with this command: \n"
            "`python manage.py load_county_limits "
            "data/county_limit_data_latest.csv --confirm=y`"
        )
    except KeyError as e:
        return (
            f"A KeyError ({e}) occurred while processing the data. "
            "If the error is a five-digit number, this could be caused by "
            "the introduction of a new county FIPS code."
        )
    except Exception as e:
        return f"{ERROR_MSG} Error: {e}\n{msg}"
    return msg
