from __future__ import absolute_import, print_function, unicode_literals

import json
import zipfile

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from collections import OrderedDict

from ratechecker.ratechecker_parameters import ParamsSerializer
from ratechecker.views import get_rates


class ScenarioValidationError(BaseException):
    pass


class ValidationError(BaseException):
    pass


class ScenarioValidator(object):
    def __init__(self, verbose=True):
        self.verbose = verbose

    def validate_file(self, scenario_file, expected_results_filename,
                      scenario_id=None):
        scenarios = ScenarioLoader().load(scenario_file)
        expected_results = ExpectedResultsLoader().load(
            expected_results_filename
        )

        if scenario_id is not None:
            scenarios = {scenario_id: scenarios[scenario_id]}

        return self.validate_scenarios(scenarios, expected_results)

    def validate_scenarios(self, scenarios, expected_results):
        failures = OrderedDict()

        for scenario_id, scenario in scenarios.items():
            if self.verbose:
                print('validating scenario', scenario_id)

            try:
                expected_result = expected_results[scenario_id]
                self.validate_scenario(scenario, expected_result)
            except ScenarioValidationError as e:
                failures[scenario_id] = e

        if failures:
            raise ValidationError(failures)

    def validate_scenario(self, scenario, expected_result):
        serializer = ParamsSerializer(data=scenario)
        serializer.is_valid(raise_exception=True)

        rates = get_rates(serializer.validated_data, data_load_testing=True)
        computed_rate = rates.get('data')

        expected_rate, expected_points = expected_result

        if not expected_rate and not computed_rate:
            if self.verbose:
                print('expected no data, got no data')
            return

        if expected_rate is not None and computed_rate is not None:
            computed_points = computed_rate.get(expected_rate)
            if expected_points == computed_points:
                if self.verbose:
                    print('expected {}/{}, computation matches'.format(
                        expected_rate,
                        expected_points,
                    ))
                return

        if self.verbose:
            print('failure: expected {}, got {}'.format(
                expected_result,
                computed_rate
            ))

        raise ScenarioValidationError(computed_rate, expected_result)


class ScenarioLoader(object):
    def load(self, f):
        scenarios = OrderedDict()

        for row in f:
            scenario = json.loads(row)
            scenario_id = scenario.pop('scenario_id')
            scenarios[scenario_id] = scenario

        return scenarios


class ExpectedResultsLoader(object):
    archive_filename = 'CoverSheet.xml'

    def load(self, filename):
        if filename.endswith('.zip'):
            return self.load_from_archive(filename)
        else:
            with open(filename) as f:
                return self.load_from_file(f)

    def load_from_archive(self, filename):
        with zipfile.ZipFile(filename) as zf:
            with zf.open(self.archive_filename) as f:
                return self.load_from_file(f)

    def load_from_file(self, f):
        tree = ET.parse(f)

        results = OrderedDict()
        for scenario in tree.getiterator(tag='Scenario'):
            scenario_data = {elem.tag: elem.text for elem in scenario}
            scenario_id = int(scenario_data['ScenarioNo'])

            results[scenario_id] = (
                scenario_data['AdjustedRates'] or None,
                scenario_data['AdjustedPoints'] or None
            )

        return results
