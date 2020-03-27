import json
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

    def print(self, *args, **kwargs):
        if self.verbose:  # pragma: no cover
            print(*args, **kwargs)

    def validate_file(self, scenario_file, dataset, scenario_id=None):
        scenarios = ScenarioLoader().load(scenario_file)
        expected_results = dataset.cover_sheet.expected_scenario_results

        if scenario_id is not None:
            scenarios = {scenario_id: scenarios[scenario_id]}

        return self.validate_scenarios(scenarios, expected_results)

    def validate_scenarios(self, scenarios, expected_results):
        failures = OrderedDict()

        for scenario_id, scenario in scenarios.items():
            self.print("validating scenario", scenario_id)

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
        computed_rates = rates.get("data")

        return self.compare_result(computed_rates, expected_result)

    def compare_result(self, computed_rates, expected_result):
        if not computed_rates:
            self.print("no rates computed for this scenario, skipping")
            return

        expected_rate, expected_points = expected_result

        if expected_rate is None:
            self.print("no rates expected for this scenario, skipping")
            return

        if computed_rates.get(expected_rate) == expected_points:
            self.print("scenario matches: ", expected_result, computed_rates)
            return

        raise ScenarioValidationError(computed_rates, expected_result)


class ScenarioLoader(object):
    @classmethod
    def load(cls, f):
        scenarios = OrderedDict()

        for row in f:
            scenario = json.loads(row)
            scenario_id = scenario.pop("scenario_id")
            scenarios[scenario_id] = scenario

        return scenarios
