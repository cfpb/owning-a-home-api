from collections import OrderedDict
from django.core.files.base import ContentFile
from unittest import TestCase

from ratechecker.validation import ExpectedResultsLoader


class TestExpectedResultsLoader(TestCase):
    def setUp(self):
        self.loader = ExpectedResultsLoader()

    def test_load_from_file_empty(self):
        f = ContentFile('<data></data>')
        self.assertEqual(self.loader.load_from_file(f), OrderedDict())

    def test_load_from_file_no_results(self):
        f = ContentFile((
            '<data><Scenarios><Scenario>'
            '<ScenarioNo>99</ScenarioNo>'
            '<AdjustedRates/>'
            '<AdjustedPoints/>'
            '</Scenario></Scenarios></data>'
        ))
        results = self.loader.load_from_file(f)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[99], (None, None))

    def test_load_from_file_results(self):
        f = ContentFile((
            '<data><Scenarios><Scenario>'
            '<ScenarioNo>1</ScenarioNo>'
            '<AdjustedRates>3.125</AdjustedRates>'
            '<AdjustedPoints>0.05</AdjustedPoints>'
            '</Scenario></Scenarios></data>'
        ))
        results = self.loader.load_from_file(f)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[1], ('3.125', '0.05'))

    def test_load_from_file_multiple_results(self):
        f = ContentFile((
            '<data><Scenarios>'
            '<Scenario>'
            '<ScenarioNo>6</ScenarioNo>'
            '<AdjustedRates>2.5</AdjustedRates>'
            '<AdjustedPoints>0.25</AdjustedPoints>'
            '</Scenario>'
            '<Scenario>'
            '<ScenarioNo>7</ScenarioNo>'
            '<AdjustedRates>9.99</AdjustedRates>'
            '<AdjustedPoints>-1.5</AdjustedPoints>'
            '</Scenario>'
            '</Scenarios></data>'
        ))
        results = self.loader.load_from_file(f)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[6], ('2.5', '0.25'))
        self.assertEqual(results[7], ('9.99', '-1.5'))
