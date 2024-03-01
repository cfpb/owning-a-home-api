from datetime import date, datetime
from unittest import TestCase
from unittest.mock import Mock
from xml.etree.cElementTree import ParseError

from django.core.files.base import ContentFile
from django.utils import timezone

from ratechecker.dataset import CoverSheet
from ratechecker.tests.helpers import get_sample_dataset


class TestDataset(TestCase):
    def test_cover_sheet(self):
        dataset = get_sample_dataset()
        self.assertIsInstance(dataset.cover_sheet, CoverSheet)

    def test_timestamp(self):
        dataset = get_sample_dataset(day=date(2017, 4, 3))
        self.assertEqual(
            dataset.timestamp,
            timezone.make_aware(
                datetime(2017, 4, 3, 0, 0, 0), timezone.get_current_timezone()
            ),
        )

    def test_load_calls_loaders(self):
        dataset = get_sample_dataset(
            day=date(2017, 4, 3), datasets={"20170403_key.txt": "testing"}
        )

        loader = Mock()
        loader.return_value = loader
        dataset.loaders = {"key": loader}
        dataset.load()

        loader.load.assert_called_once()

    def test_load_fails_if_dataset_missing(self):
        dataset = get_sample_dataset(
            day=date(2017, 4, 3), datasets={"20170403_key.txt": "testing"}
        )

        loader = Mock()
        loader.return_value = loader
        dataset.loaders = {"other_key": loader}

        with self.assertRaises(KeyError):
            dataset.load()

    def test_datafile(self):
        dataset = get_sample_dataset(
            day=date(2017, 4, 3),
            datasets={"20170403_something.txt": "testing"},
        )

        f = dataset.datafile("something")
        self.assertEqual(f.read(), b"testing")


class TestCoverSheet(TestCase):
    def test_null_file_raises_typeerror(self):
        with self.assertRaises(TypeError):
            CoverSheet(None)

    def test_invalid_xml_file_raises_parseerror(self):
        f = ContentFile("foo")
        with self.assertRaises(ParseError):
            CoverSheet(f)

    def test_missing_date_raises_valueerror(self):
        f = ContentFile("<data></data>")
        with self.assertRaises(ValueError):
            CoverSheet(f)

    def test_invalid_date_raises_valueerror(self):
        f = ContentFile(
            "<data>" "<ProcessDate><Date>foo</Date></ProcessDate>" "</data>"
        )
        with self.assertRaises(ValueError):
            CoverSheet(f)

    def test_missing_scenarios_raises_valueerror(self):
        f = ContentFile(
            "<data>"
            "<ProcessDate><Date>20170403</Date></ProcessDate>"
            "</data>"
        )
        with self.assertRaises(ValueError):
            CoverSheet(f)

    def test_no_scenarios_raises_valueerror(self):
        f = ContentFile(
            "<data>"
            "<ProcessDate><Date>20170403</Date></ProcessDate>"
            "<Scenarios></Scenarios>"
            "</data>"
        )
        with self.assertRaises(ValueError):
            CoverSheet(f)

    def test_date(self):
        f = ContentFile(
            "<data>"
            "<ProcessDate><Date>20170403</Date></ProcessDate>"
            "<Scenarios>"
            "<Scenario>"
            "<ScenarioNo>0</ScenarioNo>"
            "<AdjustedRates>3.25</AdjustedRates>"
            "<AdjustedPoints>1.75</AdjustedPoints>"
            "</Scenario>"
            "</Scenarios>"
            "</data>"
        )
        self.assertEqual(CoverSheet(f).date, date(2017, 4, 3))

    def test_scenarios(self):
        f = ContentFile(
            "<data>"
            "<ProcessDate><Date>20170403</Date></ProcessDate>"
            "<Scenarios>"
            "<Scenario>"
            "<ScenarioNo>0</ScenarioNo>"
            "<AdjustedRates>3.25</AdjustedRates>"
            "<AdjustedPoints>1.75</AdjustedPoints>"
            "</Scenario>"
            "<Scenario>"
            "<ScenarioNo>1</ScenarioNo>"
            "<AdjustedRates>1.90</AdjustedRates>"
            "<AdjustedPoints>3.75</AdjustedPoints>"
            "</Scenario>"
            "</Scenarios>"
            "</data>"
        )
        sheet = CoverSheet(f)
        self.assertEqual(len(sheet.expected_scenario_results), 2)
        self.assertEqual(sheet.expected_scenario_results[0], ("3.25", "1.75"))
        self.assertEqual(sheet.expected_scenario_results[1], ("1.90", "3.75"))

    def test_empty_scenario(self):
        f = ContentFile(
            "<data>"
            "<ProcessDate><Date>20170403</Date></ProcessDate>"
            "<Scenarios>"
            "<Scenario>"
            "<ScenarioNo>0</ScenarioNo>"
            "<AdjustedRates/>"
            "<AdjustedPoints/>"
            "</Scenario>"
            "</Scenarios>"
            "</data>"
        )
        sheet = CoverSheet(f)
        self.assertEqual(len(sheet.expected_scenario_results), 1)
        self.assertEqual(sheet.expected_scenario_results[0], (None, None))
