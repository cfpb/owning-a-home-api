import json
import os
import tempfile
import unittest
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from unittest import mock
from model_bakery import baker
from rest_framework import status

from countylimits.data_collection.county_data_monitor import (
    check_for_county_changes,
    get_base_log,
    get_current_log,
    get_lines,
    store_change_log,
)
from countylimits.data_collection.gather_county_data import (
    CHUMS_MAP,
    ERROR_MSG,
    download_datafile,
    dump_to_csv,
    get_chums_data,
    translate_data,
)
from countylimits.management.commands import load_county_limits
from countylimits.models import County, CountyLimit, State


BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + "/"


class DataAutomationTests(unittest.TestCase):
    def setUp(self):
        stdout_patch = mock.patch("sys.stdout")
        stdout_patch.start()
        self.addCleanup(stdout_patch.stop)

    def test_translate_data(self):
        test_list = [
            "9999900000NON-METRO                                         203B S02070000275665035295004266250530150AK050ALASKA                    BETHEL CENSUS A201611292017010102080002015    "  # noqa
        ]
        expected_dict = {
            "county-fips": "050",
            "limit-1-unit": "0275665",
            "limit-2-units": "0352950",
            "county-transaction-date": "20161129",
            "metro-name": "NON-METRO",
            "metro-code": "00000",
            "year-for-median-determining-limit": "2015",
            "median-price-determining-limit": "0208000",
            "county-name": "BETHEL CENSUS A",
            "state": "AK",
            "program": "203B",
            "limit-type": "S",
            "median-price": "0207000",
            "limit-4-units": "0530150",
            "limit-transaction-date": "20170101",
            "msa-code": "99999",
            "limit-3-units": "0426625",
            "state-name": "ALASKA",
        }  # noqa
        result = translate_data(test_list, CHUMS_MAP)[0]
        for key in ["county-fips", "metro-name", "county-name", "state"]:
            self.assertEqual(result[key], expected_dict[key])
        self.assertEqual(len(result), len(expected_dict))

    @mock.patch(
        "countylimits.data_collection.gather_county_data.download_datafile"
    )
    @mock.patch(
        "countylimits.data_collection.gather_county_data.translate_data"
    )
    @mock.patch("countylimits.data_collection.gather_county_data.dump_to_csv")
    def test_get_chums(self, mock_dump, mock_translate, mock_download):
        mock_download.return_value = "1\r\n2\r\n3\r\n4\r\n"
        mock_translate.return_value = [
            {
                "county-fips": "005",
                "metro-name": "Hooverville",
                "county-name": "Barbour County",
                "state": "AL",
                "limit-1-unit": "20000",
            }
        ]
        result = get_chums_data()
        self.assertNotIn("failed", result)

        self.assertEqual(mock_download.call_count, 2)
        self.assertEqual(mock_translate.call_count, 2)
        self.assertEqual(mock_dump.call_count, 4)

    @mock.patch(
        "countylimits.data_collection.gather_county_data.download_datafile"
    )
    def test_get_chums_failure(self, mock_download):
        mock_download.side_effect = ValueError("Error: 404")
        msg = get_chums_data()
        self.assertIn(ERROR_MSG, msg)

    @mock.patch(
        "countylimits.data_collection.gather_county_data.download_datafile"
    )
    def test_get_chums_download_failure(self, mock_download):
        mock_download.return_value = "Error:"
        msg = get_chums_data()
        self.assertIn(ERROR_MSG, msg)

    @mock.patch("countylimits.data_collection.gather_county_data.requests.get")
    def test_download_datafile(self, mock_get):
        return_val = mock.Mock()
        return_val.ok = True
        return_val.text = "heading1,heading2\nvalue1,value2"
        mock_get.return_value = return_val
        result = download_datafile("mockurl.example.com")
        self.assertIn("heading1", result)
        self.assertEqual(mock_get.call_count, 1)

    @mock.patch("countylimits.data_collection.gather_county_data.requests.get")
    def test_download_datafile_error(self, mock_get):
        return_val = mock.Mock()
        return_val.ok = False
        return_val.status_code = "404"
        return_val.reason = "Not found"
        mock_get.return_value = return_val
        result = download_datafile("mockurl.example.com")
        self.assertIn("404", result)
        self.assertEqual(mock_get.call_count, 1)

    @mock.patch(
        "countylimits.management.commands.oah_check_county_changes."
        "check_for_county_changes"
    )
    def test_check_county_without_email(self, mock_check):
        mock_check.return_value = "OK"
        call_command("oah_check_county_changes")
        self.assertEqual(mock_check.call_count, 1)

    @mock.patch(
        "countylimits.management.commands.oah_check_county_changes."
        "check_for_county_changes"
    )
    def test_check_county_with_email(self, mock_check):
        mock_check.return_value = "Emails were sent"
        call_command("oah_check_county_changes", "--email", "fake@example.com")
        self.assertEqual(mock_check.call_count, 1)

    @mock.patch(
        "countylimits.management.commands.gather_limit_data." "get_chums_data"
    )
    def test_gather_county_data_no_year(self, mock_get_chums):
        mock_get_chums.return_value = "Data downloaded"
        call_command("gather_limit_data")
        self.assertEqual(mock_get_chums.call_count, 1)

    @mock.patch(
        "countylimits.management.commands.gather_limit_data." "get_chums_data"
    )
    def test_gather_county_data_with_year(self, mock_get_chums):
        mock_get_chums.return_value = "Data downloaded"
        call_command("gather_limit_data", "--year", "2017")
        self.assertEqual(mock_get_chums.call_count, 1)
        mock_get_chums.assert_called_with(year=2017)


class DataCollectionTest(unittest.TestCase):
    """Test data automation functions"""

    def test_dump_to_csv(self):
        with tempfile.NamedTemporaryFile() as f:
            dump_to_csv(f.name, ["a", "b"], [{"a": "1", "b": "2"}])

            content = [line.strip() for line in open(f.name).readlines()]
            self.assertEqual(content, ["a,b", "1,2"])

    def test_get_lines(self):
        lines_in = "\n\nline 1\nline 2\n\n\nline 3\n\n"
        expected_result = ["line 1", "line 2", "line 3"]
        lines_out = get_lines(lines_in)
        self.assertEqual(lines_out, expected_result)

    def test_get_base_log(self):
        text = get_base_log()
        self.assertIn("Changes to Counties", text)

    def test_store_changelog(self):
        with tempfile.NamedTemporaryFile() as f:
            store_change_log("fake log text", to_filename=f.name)

            content = open(f.name).read().strip()
            self.assertEqual(content, "fake log text")

    @mock.patch(
        "countylimits.data_collection.county_data_monitor" ".requests.get"
    )
    @mock.patch("countylimits.data_collection.county_data_monitor.bs")
    def test_get_current_log(self, mock_bs, mock_requests):
        get_current_log()
        self.assertEqual(mock_bs.call_count, 1)
        self.assertEqual(mock_requests.call_count, 1)

    @mock.patch(
        "countylimits.data_collection.county_data_monitor.get_current_log"
    )
    @mock.patch(
        "countylimits.data_collection.county_data_monitor.get_base_log"
    )
    def test_county_data_monitor_no_change(self, mock_base, mock_current):
        with open(
            "{}data_collection/" "changelog_2017.txt".format(BASE_PATH)
        ) as f:
            mock_base.return_value = mock_current.return_value = f.read()
        self.assertIn("No county changes found", check_for_county_changes())

    @mock.patch(
        "countylimits.data_collection.county_data_monitor.get_current_log"
    )
    @mock.patch(
        "countylimits.data_collection.county_data_monitor.get_base_log"
    )
    @mock.patch(
        "countylimits.data_collection.county_data_monitor.store_change_log"
    )
    def test_county_data_monitor_with_change_no_email(
        self, mock_store_log, mock_base, mock_current
    ):
        with open(
            "{}data_collection/" "changelog_2017.txt".format(BASE_PATH)
        ) as f:
            mock_base.return_value = f.read()
            mock_current.return_value = (
                mock_base.return_value + "When dolphins fly.\n"
            )
        self.assertIn("When dolphins fly", check_for_county_changes())
        self.assertEqual(mock_current.call_count, 1)
        self.assertEqual(mock_base.call_count, 1)
        self.assertEqual(mock_store_log.call_count, 1)

    @mock.patch(
        "countylimits.data_collection.county_data_monitor.get_current_log"
    )
    @mock.patch(
        "countylimits.data_collection.county_data_monitor.get_base_log"
    )
    @mock.patch("countylimits.data_collection.county_data_monitor.send_mail")
    @mock.patch(
        "countylimits.data_collection.county_data_monitor.store_change_log"
    )
    def test_county_data_monitor_with_change_and_email(
        self, mock_store_log, mock_mail, mock_base, mock_current
    ):
        with open(
            "{}data_collection/" "changelog_2017.txt".format(BASE_PATH)
        ) as f:
            mock_base.return_value = f.read()
            mock_current.return_value = (
                mock_base.return_value + "When dolphins fly.\n"
            )
        msg = check_for_county_changes(email="fakemail@example.com")
        self.assertIn("When dolphins fly", msg)
        self.assertEqual(mock_mail.call_count, 1)
        self.assertEqual(mock_current.call_count, 1)
        self.assertEqual(mock_base.call_count, 1)
        self.assertEqual(mock_store_log.call_count, 1)


class CountyLimitTest(TestCase):
    def setUp(self):
        self.AL = baker.make(State, state_fips="01", state_abbr="AL")

        self.ALCO = baker.make(
            County,
            county_fips="001",
            county_name="Autauga County",
            state=State.objects.get(state_fips="01"),
        )

        self.ALLIM = baker.make(
            CountyLimit,
            fha_limit=Decimal("294515.00"),
            gse_limit=Decimal("453100.00"),
            va_limit=Decimal("453100.00"),
            county=County.objects.get(county_name="Autauga County"),
        )

        self.DC = baker.make(State, state_fips="11", state_abbr="DC")

        self.DCCO = baker.make(
            County,
            county_fips="001",
            county_name="District of Columbia",
            state=State.objects.get(state_fips="11"),
        )

        self.DCLIM = baker.make(
            CountyLimit,
            fha_limit=Decimal("294515.00"),
            gse_limit=Decimal("453100.00"),
            va_limit=Decimal("453100.00"),
            county=County.objects.get(county_name="District of Columbia"),
        )

        self.VA = baker.make(State, state_fips="51", state_abbr="VA")

        self.VACO = baker.make(
            County,
            county_fips="001",
            county_name="Accomack County",
            state=State.objects.get(state_fips="51"),
        )

        self.VALIM = baker.make(
            CountyLimit,
            fha_limit=Decimal("294515.00"),
            gse_limit=Decimal("453100.00"),
            va_limit=Decimal("453100.00"),
            county=County.objects.get(county_name="Accomack County"),
        )

    url = "/oah-api/county/"

    def test_county_limits_by_state__no_args(self):
        """... when state is blank"""
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"detail": "Required parameter state is missing"}
        )

    def test_county_limit_by_state__invalid_arg(self):
        """... when state has an invalid value"""
        response = self.client.get(self.url, {"state": 1234})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"state": "Invalid state"})
        response = self.client.get(self.url, {"state": "Washington DC"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"state": "Invalid state"})

    def test_county_limit_by_state__valid_arg(self):
        """... when state has a valid arg"""
        response_01 = self.client.get(self.url, {"state": "01"})
        self.assertEqual(response_01.status_code, 200)
        self.assertEqual(
            "Autauga County", response_01.data["data"][0]["county"]
        )
        response_AL = self.client.get(self.url, {"state": "AL"})
        self.assertTrue(response_01.data["data"] == response_AL.data["data"])
        response_DC = self.client.get(self.url, {"state": "DC"})
        self.assertEqual(len(response_DC.data["data"]), 1)
        response_VA = self.client.get(self.url, {"state": "VA"})
        self.assertEqual(len(response_VA.data["data"]), 1)
        self.assertEqual(
            "Accomack County", response_VA.data["data"][0]["county"]
        )

    def test_unicode(self):
        state = State.objects.get(state_fips="01")
        county = County.objects.get(county_name="Autauga County")
        county_limit = CountyLimit.objects.first()

        self.assertEqual("{}".format(state), "Alabama")
        self.assertEqual("{}".format(county), "Autauga County (001)")
        self.assertEqual(
            "{}".format(county_limit), "CountyLimit {}".format(county_limit.id)
        )


class LoadCountyLimitsTestCase(TestCase):
    def setUp(self):
        stdout_patch = mock.patch("sys.stdout")
        stdout_patch.start()
        self.c = load_county_limits.Command()
        self.out = StringIO()
        self.c.stdout = self.c.stderr = self.out
        self.test_csv = "{}data/test/test.csv".format(BASE_PATH)
        self.addCleanup(stdout_patch.stop)

    def test_handle__no_confirm(self):
        """.. check that nothing happens when confirm is not y|Y."""
        err = StringIO()
        call_command("load_county_limits", stderr=err)
        self.assertNotIn("Successfully loaded data from", err.getvalue())

    def test_handle__bad_file(self):
        """.. check that CommandError is raised when path to file is wrong."""
        self.assertRaises(
            CommandError,
            self.c.handle,
            csv="inexistent.file.csv",
            confirmed="Y",
            stdout=self.c.stderr,
        )

    def test_dump_countylimit_fixture(self):
        State.objects.create(pk=1, state_fips="xy", state_abbr="XY")

        with tempfile.NamedTemporaryFile() as f:
            load_county_limits.dump_countylimit_fixture(to_filename=f.name)

            fixture_content = open(f.name).read()
            self.assertEqual(
                json.loads(fixture_content),
                [
                    {
                        "model": "countylimits.state",
                        "pk": 1,
                        "fields": {"state_fips": "xy", "state_abbr": "XY"},
                    }
                ],
            )

    def test_handle__success(self):
        """.. check that all countylimits are loaded from CSV."""
        self.c.handle(csv=self.test_csv, confirmed="y")
        self.assertIn("Successfully loaded data", self.c.stdout.getvalue())
        self.assertEqual(CountyLimit.objects.count(), 3233)

    def test_handle__fixture_success(self):
        """.. check that all countylimits are loaded from fixture."""
        self.c.handle(confirmed="y")
        self.assertIn("Successfully loaded data", self.c.stdout.getvalue())
        self.assertEqual(CountyLimit.objects.count(), 3233)


class LoadAndDumpCountyLimitsTestCase(TestCase):
    def setUp(self):
        self.test_csv = "{}data/test/test.csv".format(BASE_PATH)
        stdout_patch = mock.patch("sys.stdout")
        stderr_patch = mock.patch("sys.stderr")
        stdout_patch.start()
        stderr_patch.start()
        self.addCleanup(stdout_patch.stop)
        self.addCleanup(stderr_patch.stop)

    @mock.patch(
        "countylimits.management.commands."
        "load_county_limits.dump_countylimit_fixture"
    )
    def test_handle__load_csv_calls_dumpdata(self, mock_dump):
        """
        check that the `--dumpdata` option calls `dump_countylimit_fixture`
        """
        loader = load_county_limits.Command()
        loader.handle(csv="latest", confirmed="y", dumpdata="true")
        self.assertEqual(mock_dump.call_count, 1)
