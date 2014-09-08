from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from countylimits.models import CountyLimit, County, State


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
        self.url = '/county/'
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
