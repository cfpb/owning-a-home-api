import json
from unittest import TestCase
from unittest.mock import patch

from django.core.files.base import ContentFile

from ratechecker.tests.helpers import get_sample_dataset
from ratechecker.validation import (
    ScenarioLoader,
    ScenarioValidationError,
    ScenarioValidator,
    ValidationError,
)


class TestScenarioValidator(TestCase):
    def setUp(self):
        self.validator = ScenarioValidator(verbose=False)
        self.scenario = {
            "scenario_id": 0,
            "loan_amount": 300000,
            "loan_term": 30,
            "loan_type": "CONF",
            "minfico": 650,
            "maxfico": 730,
            "price": 350000,
            "rate_structure": "FIXED",
            "state": "NY",
        }

    def test_validate_file(self):
        scenario_file = ContentFile(json.dumps(self.scenario))
        dataset = get_sample_dataset()

        with patch(
            "ratechecker.validation.get_rates",
            return_value={"data": {"3.25": "1.75"}},
        ):
            self.validator.validate_file(scenario_file, dataset)

    def test_validate_file_single_scenario(self):
        scenario_file = ContentFile(json.dumps(self.scenario))
        dataset = get_sample_dataset()

        with patch(
            "ratechecker.validation.get_rates",
            return_value={"data": {"3.25": "1.75"}},
        ):
            self.validator.validate_file(scenario_file, dataset, scenario_id=0)

    def test_validate_file_scenario_fails(self):
        scenario_file = ContentFile(json.dumps(self.scenario))
        dataset = get_sample_dataset()

        with patch(
            "ratechecker.validation.get_rates",
            return_value={"data": {"3.25": "0.00"}},
        ):
            with self.assertRaises(ValidationError):
                self.validator.validate_file(scenario_file, dataset)

    def test_compare_result_no_rates_computed_no_rates_expected(self):
        self.assertIsNone(
            self.validator.compare_result(
                computed_rates={}, expected_result=(None, None)
            )
        )

    def test_compare_result_no_rates_computed_rates_expected(self):
        self.assertIsNone(
            self.validator.compare_result(
                computed_rates={}, expected_result=(3.75, 0.25)
            )
        )

    def test_compare_result_rates_computed_no_rates_expected(self):
        self.assertIsNone(
            self.validator.compare_result(
                computed_rates={3.75: 0.25, 4.25: 0.5},
                expected_result=(None, None),
            )
        )

    def test_compare_result_computed_rate_matches_expected_rate(self):
        self.assertIsNone(
            self.validator.compare_result(
                computed_rates={3.75: 0.25, 4.25: 0.5},
                expected_result=(4.25, 0.5),
            )
        )

    def test_compare_result_computed_rate_does_not_match_expected_rate(self):
        with self.assertRaises(ScenarioValidationError):
            self.validator.compare_result(
                computed_rates={3.75: 0.25}, expected_result=(4.25, 0.5)
            )


class TestScenarioLoader(TestCase):
    def test_empty_file(self):
        f = ContentFile("")
        scenarios = ScenarioLoader.load(f)
        self.assertEqual(scenarios, {})

    def test_single_scenario(self):
        f = ContentFile('{"scenario_id": 3, "foo": 12, "bar": 19}')
        scenarios = ScenarioLoader.load(f)
        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[3], {"foo": 12, "bar": 19})

    def test_multiple_scenarios(self):
        f = ContentFile(
            '{"scenario_id": 3, "foo": 12, "bar": 19}\n'
            '{"scenario_id": 9, "foo": 83, "bar": 777}'
        )
        scenarios = ScenarioLoader.load(f)
        self.assertEqual(len(scenarios), 2)
        self.assertEqual(scenarios[3], {"foo": 12, "bar": 19})
        self.assertEqual(scenarios[9], {"foo": 83, "bar": 777})

    def test_no_scenario_id_raises_keyerror(self):
        f = ContentFile('{"foo": 12, "bar": 19}')
        with self.assertRaises(KeyError):
            ScenarioLoader.load(f)
