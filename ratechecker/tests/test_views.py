import json

from datetime import datetime, timedelta
from decimal import Decimal
from django.core.urlresolvers import reverse
from django.test import override_settings
from django.utils import timezone
from model_mommy import mommy
from rest_framework import status
from rest_framework.test import APITestCase

from ratechecker.models import Region, Product, Rate, Adjustment, Fee
from ratechecker.views import set_lock_max_min


class RateCheckerTestCase(APITestCase):
    def setUp(self):

        self.url = '/oah-api/rates/rate-checker'
        REGIONS = [[1, 'DC'], [2, 'VA']]
        PRODUCTS = [
            # plan_id, institution, loan_purpose, pmt_type, loan_type, loan_term, int_adj_term, _, io, _, _, _, _, _, _,
            # min_ltv, max_ltv, minfico, maxfico, min_loan_amt, max_loan_amt, single_family, condo, coop
            [11, 'Institution 1', 'PURCH', 'FIXED', 'CONF', 30, None, None, 0, None, None, None, None, None, None, 1, 95, 680, 700, 90000, 750000, 1, 0, 0],
            [22, 'Institution 2', 'PURCH', 'FIXED', 'CONF', 30, None, None, 0, None, None, None, None, None, None, 1, 87, 680, 740, 90000, 550000, 1, 0, 0],
            [33, 'Institution 3', 'PURCH', 'ARM', 'CONF', 15, 5, None, 0, None, None, None, None, None, None, 1, 95, 680, 740, 90000, 550000, 1, 0, 0],
            [44, 'Institution 4', 'PURCH', 'FIXED', 'CONF', 30, None, None, 0, None, None, None, None, None, None, 1, 87, 680, 740, 90000, 550000, 1, 0, 0],
            [55, 'Institution 5', 'PURCH', 'ARM', 'CONF', 30, 5, None, 0, None, None, None, None, None, None, 1, 87, 680, 740, 90000, 550000, 1, 0, 0],
            [66, 'Institution 6', 'PURCH', 'FIXED', 'CONF', 30, None, None, 0, None, None, None, None, None, None, 1, 87, 680, 740, 90000, 550000, 1, 0, 0],
            [77, 'Institution 7', 'PURCH', 'FIXED', 'FHA-HB', 15, None, None, 0, None, None, None, None, None, None, 1, 87, 680, 740, 90000, 550000, 1, 0, 0],
            [88, 'Institution 8', 'PURCH', 'FIXED', 'FHA', 30, None, None, 0, None, None, None, None, None, None, 1, 87, 680, 740, 90000, 550000, 1, 0, 0],
        ]
        RATES = [
            # rate_id, product_id, region_id, lock, base_rate, total_points
            [111, 11, 1, 50, '3.150', '0.5'],
            [112, 11, 2, 60, '4.350', '-0.5'],
            [113, 11, 1, 60, '2.125', '0.125'],
            [221, 22, 1, 60, '3.555', '0.125'],
            [331, 33, 1, 60, '3.250', '0.125'],
            [332, 33, 2, 60, '4.650', '-0.5'],
            [441, 44, 1, 50, '3.125', '1.25'],
            [551, 55, 1, 50, '0.125', '0.125'],
            [661, 66, 1, 60, '3.705', '0.5'],
            [771, 77, 2, 60, '1.705', '0.25'],
            [772, 77, 2, 60, '2.705', '1.25'],
            [881, 88, 1, 60, '3.000', '0.5'],
            [882, 88, 1, 60, '2.005', '0.25'],
            [883, 88, 1, 60, '1.005', '-0.25'],
        ]
        ADJUSTMENTS = [
            # rule_id, product_id, affect_rate_type, adj_value, min_loan_amt, max_loan_amt
            # prop_type, minfico, maxfico, minltv, maxltv, state
            [1, 11, 'P', '-0.35', 100000, 500000, 'CONDO', 660, 780, 30, 95, 'DC'],
            [2, 11, 'P', '0.25', 100000, 500000, 'CONDO', 660, 780, 30, 95, 'DC'],
            [3, 11, 'R', '0.15', 100000, 500000, 'CONDO', 660, 780, 30, 95, 'DC'],
            [4, 22, 'R', '0.25', 100000, 500000, 'CONDO', 660, 780, 30, 95, 'VA'],
            [5, 22, 'R', '0.15', 100000, 500000, 'CONDO', 660, 780, 30, 95, 'DC'],
            [6, 33, 'R', '0.25', 100000, 500000, 'CONDO', 660, 780, 30, 95, 'DC'],
            [7, 77, 'P', '0.125', 100000, 500000, 'CONDO', 660, 780, 30, 95, 'VA'],
        ]
        FEES = [
            # plan_id, product_id, state_id, lender , single_family, condo, coop,
            # origination_dollar, origination_percent, third_party
            [11, 11111, 'DC', 'SMPL', 1, 1, 1, 1608.0000, .000, 587.2700],
            [11, 11111, 'DC', 'SMPL1', 1, 0, 1, 1610.0000, .000, 589.2700],
            [10, 11001, 'DC', 'SMPL1', 0, 1, 0, 1610.0000, .000, 589.2700],
            [11, 11111, 'VA', 'SMPL2', 1, 1, 1, 1610.0000, .000, 589.2700],
        ]
        NOW = timezone.now()

        for region in REGIONS:
            reg = Region(region_id=region[0], state_id=region[1], data_timestamp=NOW)
            reg.save()

        for p in PRODUCTS:
            product = Product(
                plan_id=p[0], institution=p[1], loan_purpose=p[2], pmt_type=p[3],
                loan_type=p[4], loan_term=p[5], int_adj_term=p[6], adj_period=p[7], io=p[8],
                arm_index=p[9], int_adj_cap=p[10], annual_cap=p[11], loan_cap=p[12], arm_margin=p[13],
                ai_value=p[14], min_ltv=p[15], max_ltv=p[16], min_fico=p[17], max_fico=p[18],
                min_loan_amt=p[19], max_loan_amt=p[20], single_family=p[21], condo=p[22],
                coop=p[23], data_timestamp=NOW
            )
            product.save()

        for r in RATES:
            rate = Rate(
                rate_id=r[0], product_id=r[1], region_id=r[2], lock=r[3], base_rate=r[4],
                total_points=r[5], data_timestamp=NOW
            )
            rate.save()

        for a in ADJUSTMENTS:
            adjustment = Adjustment(
                rule_id=a[0], product_id=a[1], affect_rate_type=a[2],
                adj_value=a[3], min_loan_amt=a[4], max_loan_amt=a[5], prop_type=a[6],
                min_fico=a[7], max_fico=a[8], min_ltv=a[9], max_ltv=a[10], state=a[11],
                data_timestamp=NOW
            )
            adjustment.save()

        for f in FEES:
            fee = Fee(
                plan_id=f[0], product_id=f[1], state_id=f[2], lender=f[3], single_family=f[4],
                condo=f[5], coop=f[6], origination_dollar=Decimal("%s" % f[7]),
                origination_percent=Decimal("%s" % f[8]), third_party=Decimal("%s" % f[9]),
                data_timestamp=NOW
            )
            fee.save()

    def test_set_lock_max_min(self):
        """Make sure max and min are set"""
        locks = {
            60: {'lock': '60', 'minval': 46},
            45: {'lock': '45', 'minval': 31},
            30: {'lock': '30', 'minval': 0}
        }
        for key in locks.keys():
            mock_data = set_lock_max_min(locks[key])
            self.assertEqual(mock_data['max_lock'], key)
            self.assertEqual(mock_data['min_lock'], locks[key]['minval'])

    def test_rate_checker__no_args(self):
        """... when no parameters provided """
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get('%s-fees' % self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_checker__valid(self):
        """... when valid parameters are provided """
        params = {
            'state': 'DC',
            'loan_purpose': 'PURCH',
            'rate_structure': 'FIXED',
            'loan_type': 'CONF',
            'max_ltv': 50,
            'min_ltv': 50,
            'loan_term': 30,
            'loan_amount': 160000,
            'price': 320000,
            'maxfico': 700,
            'minfico': 700,
            'max_lock': 60,
            'min_lock': 45,
            'property_type': 'CONDO',
            'arm_type': '5-1',
            'io': 0
        }
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('data')), 2)
        self.assertEqual(response.data.get('data').get('2.275'), 1)
        self.assertEqual(response.data.get('data').get('3.705'), 2)
        # self.assertTrue(result)
        # self.assertEqual(len(result), 2)
        # self.assertEqual(len(result['data']), 2)
        # self.assertEqual(result['data']['2.275'], 1)
        # self.assertEqual(result['data']['3.705'], 2)
        # self.assertFalse(response_fixed.data.get('data') is None)
        # self.assertEqual(response_fixed.data.get('data').get('monthly'), 1.5)
        # self.assertTrue(response_fixed.data.get('data').get('upfront') is None)

        response = self.client.get('%s-fees' % self.url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('fees' in response.data)
        self.assertEqual(len(response.data['fees']), 3)

        threshold = 0.01
        odollar = abs(response.data['fees']['origination_dollar'] - 1608.0)
        self.assertTrue(odollar < threshold)
        self.assertEqual(response.data['fees']['origination_percent'], 0.0)
        tparty = abs(response.data['fees']['third_party'] - 587.27)
        self.assertTrue(tparty < threshold)


@override_settings(URLCONF='ratechecker.urls')
class RateCheckerStatusTest(APITestCase):
    def get(self):
        return self.client.get(
            reverse('rate-checker-status'),
            headers={'Accepts': 'application/json'}
        )

    def test_no_data_returns_200(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_no_data_returns_json(self):
        response = self.get()
        self.assertEqual(response['Content-type'], 'application/json')

    def test_no_data_returns_none(self):
        response = self.get()
        self.assertEqual(json.loads(response.content), {'load': None})

    def test_data_returns_200(self):
        mommy.make(Region)
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_data_returns_json(self):
        mommy.make(Region)
        response = self.get()
        self.assertEqual(response['Content-type'], 'application/json')

    def test_data_returns_timestamp(self):
        region = mommy.make(Region)
        response = self.get()
        ts = datetime.strptime(
            json.loads(response.content)['load'],
            '%Y-%m-%dT%H:%M:%S.%fZ'
        )
        ts = timezone.make_aware(ts, timezone=timezone.utc)

        # These might not match exactly due to ISO8601 JSON formatting.
        self.assertTrue(abs(ts - region.data_timestamp) < timedelta(seconds=1))

    def test_data_format_iso8601(self):
        timestamp = datetime(2017, 1, 2, 3, 4, 56, tzinfo=timezone.utc)
        mommy.make(Region, data_timestamp=timestamp)
        response = self.get()
        self.assertIn('2017-01-02T03:04:56Z', response.content)
