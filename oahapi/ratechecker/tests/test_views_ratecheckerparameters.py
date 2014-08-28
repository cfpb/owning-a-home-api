from django.test import TestCase

from ratechecker.views import RateCheckerParameters


class RateCheckerParametersTestCase(TestCase):

    def setUp(self):
        self.rcp = RateCheckerParameters()

    def test_calculate_locks__default(self):
        """ ... calculate_locks with a default value of self.lock."""
        self.assertEqual(self.rcp.min_lock, 46)
        self.assertEqual(self.rcp.max_lock, 60)

    def test_calculate_locks__valid(self):
        """ ... calculate_locks with a valid value of self.lock."""
        self.rcp.lock = 30
        self.rcp.calculate_locks()
        self.assertEqual(self.rcp.min_lock, 0)
        self.assertEqual(self.rcp.max_lock, 30)

    def test_calculate_locks__invalid_integer(self):
        """ ... calculate_locks with an invalid value."""
        self.rcp.lock = 10
        self.assertRaises(KeyError, self.rcp.calculate_locks)

    def test_calculate_locks__invalid_string(self):
        """ ... calculate_locks with an invalid value."""
        self.rcp.lock = 'A'
        self.assertRaises(KeyError, self.rcp.calculate_locks)

    def test_set_loan_amount__empty(self):
        """ ... set_loan_amount with an empty string as amount."""
        self.assertFalse(hasattr(self.rcp, 'loan_amount'))
        self.assertRaises(ValueError, self.rcp.set_loan_amount, "")
        self.assertFalse(hasattr(self.rcp, 'loan_amount'))

    def test_set_loan_amount__null(self):
        """ ... set_loan_amount with a null value."""
        self.assertFalse(hasattr(self.rcp, 'loan_amount'))
        self.assertRaises(TypeError, self.rcp.set_loan_amount, None)
        self.assertFalse(hasattr(self.rcp, 'loan_amount'))

    def test_set_loan_amount__valid(self):
        """ ... set_loan_amount with a valid value."""
        loan_amount = 10000
        self.rcp.set_loan_amount(loan_amount)
        self.assertTrue(hasattr(self.rcp, 'loan_amount'))
        self.assertEqual(self.rcp.loan_amount, loan_amount)

    def test_set_loan_amount__negative(self):
        """ ... set_loan_amount with a negative value."""
        loan_amount = -10000
        self.rcp.set_loan_amount(loan_amount)
        self.assertTrue(hasattr(self.rcp, 'loan_amount'))
        self.assertEqual(self.rcp.loan_amount, abs(loan_amount))

    def test_set_price__empty(self):
        """ ... set_price with an empty argument."""
        self.assertRaises(ValueError, self.rcp.set_price, "")
        self.assertFalse(hasattr(self.rcp, 'price'))

    def test_set_price__null(self):
        """ ... set_price with a null argument."""
        self.assertRaises(TypeError, self.rcp.set_price, None)
        self.assertFalse(hasattr(self.rcp, 'price'))

    def test_set_price__valid(self):
        """ ... set_price with a valid argument."""
        price = 10000
        self.rcp.set_price(price)
        self.assertTrue(hasattr(self.rcp, 'price'))
        self.assertEqual(self.rcp.price, price)

    def test_set_price__negative(self):
        """ ... set_price with a negative argument."""
        price = -10000
        self.rcp.set_price(price)
        self.assertTrue(hasattr(self.rcp, 'price'))
        self.assertEqual(self.rcp.price, abs(price))

    def test_set_state__empty(self):
        """ ... set_state with an empty value."""
        state = ""
        self.rcp.set_state(state)
        self.assertTrue(hasattr(self.rcp, 'state'))
        self.assertEqual(self.rcp.state, state)

    def test_set_state__null(self):
        """ .. set_state with a null value."""
        state = None
        self.rcp.set_state(state)
        self.assertTrue(hasattr(self.rcp, 'state'))
        self.assertTrue(self.rcp.state is None)

    def test_set_state__number(self):
        """ .. set_state with a number value."""
        state = 123
        self.rcp.set_state(state)
        self.assertEqual(self.rcp.state, state)

    def test_set_state__state_name(self):
        """ .. set_state with a state name as value."""
        state = "District of Columbia"
        self.rcp.set_state(state)
        self.assertEqual(self.rcp.state, state)

    def test_set_state__state_abbr(self):
        """ .. set_state with a state abbr as value."""
        state = "DC"
        self.rcp.set_state(state)
        self.assertEqual(self.rcp.state, state)

    def test_set_loan_type__empty(self):
        """ .. set_loan_type with an empty value."""
        self.assertRaises(ValueError, self.rcp.set_loan_type, "")
        self.assertFalse(hasattr(self.rcp, 'loan_type'))

    def test_set_loan_type__null(self):
        """ .. set_loan_type with a null value."""
        self.assertRaises(AttributeError, self.rcp.set_loan_type, None)
        self.assertFalse(hasattr(self.rcp, 'loan_type'))

    def test_set_loan_type__valid(self):
        """ .. set_loan_type with a valid value."""
        loan_type = "fHa"
        self.rcp.set_loan_type(loan_type)
        self.assertEqual(self.rcp.loan_type, loan_type.upper())

    def test_set_loan_type__invalid(self):
        """ .. set_loan_type with an invalid value."""
        self.assertRaises(ValueError, self.rcp.set_loan_type, 'Not A Loan Type')

    def test_set_ficos__empty(self):
        """ .. set_ficos with empty args."""
        self.assertRaises(ValueError, self.rcp.set_ficos, "", "")
        self.assertFalse(hasattr(self.rcp, 'minfico'))
        self.assertFalse(hasattr(self.rcp, 'maxfico'))

    def test_set_ficos__valid(self):
        """ .. set_ficos with valid values."""
        maxfico, minfico = 800, 700
        self.rcp.set_ficos(minfico, maxfico)
        self.assertTrue(self.rcp.maxfico == maxfico - 1)
        self.assertTrue(self.rcp.minfico == minfico)

    def test_set_ficos__max_smaller(self):
        """ .. set_ficos with maxfico < minfico."""
        maxfico, minfico = 600, 700
        self.rcp.set_ficos(minfico, maxfico)
        self.assertTrue(self.rcp.maxfico == minfico - 1)
        self.assertTrue(self.rcp.minfico == maxfico)

    def test_set_ficos__equal(self):
        """ .. set_ficos with maxfico = minfico."""
        maxfico = minfico = 900
        self.rcp.set_ficos(minfico, maxfico)
        self.assertTrue(self.rcp.maxfico == minfico)
        self.assertTrue(self.rcp.minfico == self.rcp.maxfico)

    def test_set_ficos__negative(self):
        """ .. set_ficos with negative values."""
        maxfico = -100
        minfico = -200
        self.rcp.set_ficos(minfico, maxfico)
        self.assertTrue(self.rcp.maxfico == abs(minfico) - 1)
        self.assertTrue(self.rcp.minfico == abs(maxfico))

    def test_set_rate_structure__invalid(self):
        """ .. set_rate_structure with empty args."""
        self.assertRaises(ValueError, self.rcp.set_rate_structure, "", 1)
        self.assertRaises(AttributeError, self.rcp.set_rate_structure, None, 1)
        self.assertRaises(AttributeError, self.rcp.set_rate_structure, 123, 1)

    def test_set_rate_structure__valid(self):
        """ .. set_rate_structure with rate_structure = fixed, random arm_type."""
        rate_structure = "fIXed"
        arm_type = ""
        self.rcp.set_rate_structure(rate_structure, arm_type)
        self.assertTrue(hasattr(self.rcp, 'rate_structure'))
        self.assertEqual(self.rcp.rate_structure, rate_structure.upper())
        self.assertFalse(hasattr(self.rcp, 'arm_type'))

    def test_set_rate_structure__invalid_arm_type(self):
        """ .. set_rate_structure with rate_structure = arm, invalid arm_type."""
        rate_structure = "arm"
        arm_type = ""
        self.assertRaises(ValueError, self.rcp.set_rate_structure, rate_structure, arm_type)
        self.assertTrue(hasattr(self.rcp, 'rate_structure'))
        self.assertEqual(self.rcp.rate_structure, rate_structure.upper())
        self.assertFalse(hasattr(self.rcp, 'arm_type'))

    def test_set_rate_structure__valid_arm_type(self):
        """ .. set_rate_structure with rate_structure = arm, invalid arm_type."""
        rate_structure = "arm"
        arm_type = "3-1"
        self.rcp.set_rate_structure(rate_structure, arm_type)
        self.assertTrue(hasattr(self.rcp, 'rate_structure'))
        self.assertEqual(self.rcp.rate_structure, rate_structure.upper())
        self.assertTrue(hasattr(self.rcp, 'arm_type'))
        self.assertEqual(self.rcp.arm_type, arm_type)

    def test_set_loan_term__empty(self):
        """ .. set_loan_term with an empty arg."""
        self.assertRaises(ValueError, self.rcp.set_loan_term, "")

    def test_set_loan_term__valid(self):
        loan_term = 15
        self.rcp.set_loan_term(loan_term)
        self.assertEqual(self.rcp.loan_term, loan_term)

    def test_set_loan_term__negative(self):
        loan_term = -15
        self.rcp.set_loan_term(loan_term)
        self.assertEqual(self.rcp.loan_term, abs(loan_term))

    def test_calculate_loan_to_value(self):
        """ calculates using internal values, so only checking the formula."""
        self.rcp.price = 200000
        self.rcp.loan_amount = 180000
        self.rcp.calculate_loan_to_value()
        self.assertEqual(self.rcp.min_ltv, 90)
        self.assertTrue(self.rcp.min_ltv == self.rcp.max_ltv)

    def test_set_from_query_params__empty(self):
        """ .. set_from_query_params with an empty query."""
        self.assertRaises(TypeError, self.rcp.set_from_query_params, "")

    def test_set_from_query_params__valid(self):
        query = {
            'loan_amount': 180000, 'price': 200000, 'state': 'dc', 'loan_type': 'conF',
            'maxfico': 700, 'minfico': 700, 'loan_term': 30, 'rate_structure': 'fixED',
            'arm_type': '3-1'
        }
        self.rcp.set_from_query_params(query)
        self.assertEqual(self.rcp.loan_amount, query['loan_amount'])
        self.assertEqual(self.rcp.price, query['price'])
        self.assertEqual(self.rcp.state, query['state'])
        self.assertEqual(self.rcp.loan_type, query['loan_type'].upper())
        self.assertEqual(self.rcp.maxfico, query['maxfico'])
        self.assertEqual(self.rcp.minfico, query['minfico'])
        self.assertEqual(self.rcp.loan_term, query['loan_term'])
        self.assertEqual(self.rcp.rate_structure, query['rate_structure'].upper())
        self.assertFalse(hasattr(self.rcp, 'arm_type'))
