import os
import shutil

from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase
from django.utils.six import StringIO

from countylimits.models import CountyLimit, County, State
from countylimits.management.commands.load_county_limits import Command


class CountyLimitTest(APITestCase):
    def populate_db(self):
        """ Prepopulate DB with dummy data. """
        sDC = State(state_abbr='DC', state_fips=11)
        sDC.save()
        sVA = State(state_abbr='VA', state_fips=22)
        sVA.save()
        cDC1 = County(county_name='DC County 1', county_fips=333, state_id=sDC.id)
        cDC1.save()
        cDC2 = County(county_name='DC County 2', county_fips=444, state_id=sDC.id)
        cDC2.save()
        cVA1 = County(county_name='VA County 1', county_fips=555, state_id=sVA.id)
        cVA1.save()
        cl1 = CountyLimit(county=cDC1, fha_limit=1, gse_limit=1, va_limit=1)
        cl1.save()
        cl2 = CountyLimit(county=cDC2, fha_limit=10, gse_limit=10, va_limit=10)
        cl2.save()
        cl3 = CountyLimit(county=cVA1, fha_limit=100, gse_limit=100, va_limit=100)
        cl3.save()

    def setUp(self):
        self.url = '/oah-api/county/'
        self.populate_db()

    def test_county_limits_by_state__no_args(self):
        """ ... when state is blank """
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Required parameter state is missing'})

    def test_county_limit_by_state__invalid_arg(self):
        """ ... when state has an invalid value """
        response = self.client.get(self.url, {'state': 123})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'data': [], 'request': {'state': '123'}})
        response = self.client.get(self.url, {'state': 'Washington DC'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'data': [], 'request': {'state': 'Washington DC'}})

    def test_county_limit_by_state__valid_arg(self):
        """ ... when state has a valid arg """
        response_11 = self.client.get(self.url, {'state': 11})
        self.assertEqual(response_11.status_code, status.HTTP_200_OK)
        self.assertFalse(not response_11.data['data'])

        response_DC = self.client.get(self.url, {'state': 'DC'})
        self.assertEqual(len(response_11.data['data']), 2)
        self.assertTrue(response_11.data['data'] == response_DC.data['data'])

        response_VA = self.client.get(self.url, {'state': 'VA'})
        self.assertTrue(len(response_VA.data['data']) == 1)
        self.assertFalse(response_11.data['data'] == response_VA.data['data'])

    def test_unicode(self):
        state = State.objects.all()[0]
        county = County.objects.all()[0]
        county_limit = CountyLimit.objects.all()[0]

        self.assertEqual('%s' % state, 'District of Columbia')
        self.assertEqual('%s' % county, 'DC County 1 (333)')
        self.assertEqual('%s' % county_limit, 'CountyLimit %s' % county_limit.id)


class LoadCountyLimitsTestCase(TestCase):

    def prepare_sample_data(self, filename):
        with open(filename, 'w') as data:
            data.write("Header to be skipped\n")
            data.write('DC,01,001,01001,DC County 1,417000,271050,417000\n')
            data.write('DC,01,002,01002,DC County 2,417000,271050,417000\n')
            data.close()

    def setUp(self):
        self.c = Command()
        self.out = StringIO()
        self.c.stdout = self.c.stderr = self.out

        self.test_dir = '%s/test_folder' % os.path.dirname(os.path.realpath(__file__))
        os.mkdir(self.test_dir)
        os.chdir(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_handle__no_confirm(self):
        """ .. check that nothing happens when confirm is not y|Y."""
        self.c.handle(stdout=self.out)
        self.assertNotIn(self.out.getvalue(), 'Successfully loaded data from')

    def test_handle__no_arguments(self):
        """ .. check that CommandError is raised."""
        self.assertRaises(CommandError, self.c.handle, confirmed='y', stdout=self.out)

    def test_handle__success(self):
        """ .. check that all countylimits are loaded."""
        fname = 'county-limits.csv'
        self.prepare_sample_data(fname)
        self.c.handle('%s/%s' % (self.test_dir, fname), confirmed='Y')
        self.assertIn('Successfully loaded data from %s/%s' % (self.test_dir, fname), self.out.getvalue())
        county_limits = CountyLimit.objects.all()
        self.assertEqual(len(county_limits), 2)
