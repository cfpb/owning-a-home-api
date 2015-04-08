from django.test import TestCase

from decimal import Decimal

from ratechecker.models import Product
from ratechecker.ratechecker_parameters import ParamsSerializer


class RateCheckerParametersTestCase(TestCase):

    def setUp(self):
        self.data = {
                    'price' : 240000,
                    'loan_amount': 200000,
                    'state': 'GA',
                    'loan_type': 'JUMBO',
                    'minfico': 700,
                    'maxfico': 800,
                    'rate_structure': 'FIXED',
                    'loan_term': 30,
        }

    def test_is_valid__no_args(self):
        serializer = ParamsSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 8)
        self.assertEqual(serializer.errors.get('price'), [u'This field is required.'])
        self.assertEqual(serializer.errors.get('loan_amount'), [u'This field is required.'])
        self.assertEqual(serializer.errors.get('state'), [u'This field is required.'])
        self.assertEqual(serializer.errors.get('loan_type'), [u'This field is required.'])
        self.assertEqual(serializer.errors.get('minfico'), [u'This field is required.'])
        self.assertEqual(serializer.errors.get('maxfico'), [u'This field is required.'])
        self.assertEqual(serializer.errors.get('rate_structure'), [u'This field is required.'])
        self.assertEqual(serializer.errors.get('loan_term'), [u'This field is required.'])

    def test_is_valid__valid_args(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('price'), Decimal('240000'))
        self.assertEqual(serializer.data.get('loan_amount'), Decimal('200000'))
        self.assertEqual(serializer.data.get('state'), 'GA')
        self.assertEqual(serializer.data.get('loan_type'), 'JUMBO')
        self.assertEqual(serializer.data.get('minfico'), 700)
        self.assertEqual(serializer.data.get('maxfico'), 800)
        self.assertEqual(serializer.data.get('rate_structure'), 'FIXED')
        self.assertEqual(serializer.data.get('loan_term'), 30)

    def test_is_valid__invalid_lock(self):
        self.data['lock'] = 20
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors.get('lock'), [u'lock needs to be 30, 45, or 60.'])

    def test_is_valid__lock_default(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('lock'), ParamsSerializer.LOCK)
        self.assertEqual(serializer.data.get('min_lock'), 46)
        self.assertEqual(serializer.data.get('max_lock'), 60)

    def test_is_valid__lock_non_default(self):
        self.data['lock'] = 30
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('lock'), 30)
        self.assertEqual(serializer.data.get('min_lock'), 0)
        self.assertEqual(serializer.data.get('max_lock'), 30)

    def test_is_valid__points_default(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('points'), ParamsSerializer.POINTS)

    def test_is_valid__points_non_default(self):
        self.data['points'] = 4
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('points'), 4)

    def test_is_valid__property_type_default(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('property_type'), ParamsSerializer.PROPERTY_TYPE)

    def test_is_valid__property_type_non_default(self):
        self.data['property_type'] = ParamsSerializer.PROPERTY_TYPE_COOP
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('property_type'), ParamsSerializer.PROPERTY_TYPE_COOP)

    def test_is_valid__property_type_invalid(self):
        self.data['property_type'] = 'A'
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors.get('property_type'), [u'Select a valid choice. A is not one of the available choices.'])

    def test_is_valid__loan_purpose_default(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('loan_purpose'), ParamsSerializer.LOAN_PURPOSE)

    def test_is_valid__loan_purpose_non_default(self):
        self.data['loan_purpose'] = Product.REFI
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('loan_purpose'), Product.REFI)

    def test_is_valid__loan_purpose_invalid(self):
        self.data['loan_purpose'] = 'A'
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors.get('loan_purpose'), [u'Select a valid choice. A is not one of the available choices.'])

    def test_is_valid__io_default(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('io'), ParamsSerializer.IO)

    def test_is_valid__io_non_default(self):
        self.data['io'] = 1
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('io'), 1)

    def test_is_valid__io_invalid(self):
        self.data['io'] = 4
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors.get('io'), [u'io needs to be 0 or 1.'])

    def test_is_valid__loan_amount_none(self):
        self.data['loan_amount'] = None
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors.get('loan_amount'), [u'This field is required.'])

    def test_is_valid__loan_amount_empty(self):
        self.data['loan_amount'] = ''
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors.get('loan_amount'), [u'This field is required.'])

    def test_is_valid__loan_amount_negative(self):
        self.data['loan_amount'] = -10000
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('loan_amount'), Decimal('10000'))

    def test_is_valid__price_negative(self):
        self.data['price'] = -10000
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('price'), Decimal('10000'))

    def test_is_valid__state_invalid(self):
        self.data['state'] = 123
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors.get('state'), [u'Select a valid choice. 123 is not one of the available choices.'])

    def test_is_valid__loan_type_invalid(self):
        self.data['loan_type'] = 'A'
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors.get('loan_type'), [u'Select a valid choice. A is not one of the available choices.'])

    def test_is_valid__maxfico_smaller(self):
        self.data['maxfico'] = 600
        self.data['minfico'] = 700
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('maxfico'), 700)
        self.assertEqual(serializer.data.get('minfico'), 600)

    def test_is_valid__ficos_negative(self):
        self.data['maxfico'] = -100
        self.data['minfico'] = -200
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('maxfico'), 200)
        self.assertEqual(serializer.data.get('minfico'), 100)

    def test_is_valid__rate_structure_arm_no_arm_type(self):
        self.data['rate_structure'] = 'ARM'
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors.get('non_field_errors'), [u'arm_type is required if rate_structure is ARM.'])

    def test_is_valid__loan_term_negative(self):
        self.data['loan_term'] = -30
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('loan_term'), 30)

    def test_is_valid__ltv__without_ltv(self):
        self.data['price'] = 200000
        self.data['loan_amount'] = 180000
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get('min_ltv'), 90)
        self.assertTrue(serializer.data.get('min_ltv'), serializer.data.get('max_ltv'))


    # # def test_calculate_loan_to_value__with_ltv(self):
    # #     """ calculates using internal values, so only checking the formula."""
    # #     self.rcp.price = 1 # @TODO price will crash if 0
    # #     self.rcp.loan_amount = 0
    # #     ltv = 80
    # #     self.rcp.calculate_loan_to_value(ltv)
    # #     self.assertEqual(self.rcp.min_ltv, ltv)
    # #     self.assertTrue(self.rcp.min_ltv == self.rcp.max_ltv)
