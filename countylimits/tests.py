import os
from rest_framework import status
from django.test import TestCase
from django.utils.six import StringIO

from countylimits.models import CountyLimit, County, State
from countylimits.management.commands.load_county_limits import Command
from django.core.management.base import CommandError

try:
    BASE_PATH = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))) + '/'
except:
    BASE_PATH = ''


class CountyLimitTest(TestCase):

    fixtures = [
        '{}countylimits/fixtures/countylimit_data.json'.format(BASE_PATH)
        ]

    url = '/oah-api/county/'

    def test_county_limits_by_state__no_args(self):
        """ ... when state is blank """
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {'detail': 'Required parameter state is missing'})

    def test_county_limit_by_state__invalid_arg(self):
        """ ... when state has an invalid value """
        response = self.client.get(self.url, {'state': 1234})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'state': 'Invalid state'})
        response = self.client.get(self.url, {'state': 'Washington DC'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'state': 'Invalid state'})

    def test_county_limit_by_state__valid_arg(self):
        """ ... when state has a valid arg """
        response_11 = self.client.get(self.url, {'state': 11})
        self.assertEqual(response_11.status_code, status.HTTP_200_OK)
        self.assertEqual('District of Columbia',
                         response_11.data['data'][0]['county'])
        response_DC = self.client.get(self.url, {'state': 'DC'})
        self.assertEqual(len(response_DC.data['data']), 1)
        self.assertTrue(response_11.data['data'] == response_DC.data['data'])
        response_VA = self.client.get(self.url, {'state': 'VA'})
        self.assertEqual(len(response_VA.data['data']), 134)
        self.assertEqual('Accomack County',
                         response_VA.data['data'][0]['county'])

    def test_unicode(self):
        state = State.objects.first()
        county = County.objects.first()
        county_limit = CountyLimit.objects.first()

        self.assertEqual('{}'.format(state), 'Alabama')
        self.assertEqual('{}'.format(county), 'Autauga County (001)')
        self.assertEqual(
            '{}'.format(county_limit),
            'CountyLimit {}'.format(county_limit.id))


class LoadCountyLimitsTestCase(TestCase):

    fixtures = [
        '{}countylimits/fixtures/countylimit_data.json'.format(BASE_PATH)
        ]

    c = Command()
    out = StringIO()

    test_csv = '{}data/test/test.csv'.format(BASE_PATH)

    def setUp(self):
        self.c.stdout = self.c.stderr = self.out

    def test_handle__no_confirm(self):
        """ .. check that nothing happens when confirm is not y|Y."""
        self.c.handle(stderr=self.out)
        self.assertNotIn(self.c.stdout.getvalue(),
                         'Successfully loaded data from')

    def test_handle__no_arguments(self):
        """ .. check that CommandError is raised."""
        self.assertRaises(
            CommandError,
            self.c.handle,
            confirmed='y',
            stdout=self.c.stderr)

    def test_handle__bad_file(self):
        """ .. check that CommandError is raised when path to file is wrong."""
        self.assertRaises(
            CommandError,
            self.c.handle,
            'inexistent.file.csv',
            confirmed='Y',
            stdout=self.c.stderr)

    def test_handle__success(self):
        """ .. check that all countylimits are loaded."""
        self.c.handle(self.test_csv, confirmed='Y')
        self.assertIn(
            'Successfully loaded data from {}'.format(self.test_csv),
            self.c.stdout.getvalue())
        self.assertEqual(CountyLimit.objects.count(), 3234)
