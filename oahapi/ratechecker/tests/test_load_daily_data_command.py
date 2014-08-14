from decimal import Decimal
from datetime import datetime
from django.test import TestCase

from ratechecker.management.commands.load_daily_data import Command


class LoadDailyTestCase(TestCase):

    def test_string_to_boolean(self):
        c = Command()

        b = c.string_to_boolean('abc')
        self.assertEqual(b, None)

        b = c.string_to_boolean('False')
        self.assertFalse(b)

        b = c.string_to_boolean('True')
        self.assertTrue(True)

    def test_nullable_int(self):
        c = Command()
        self.assertEqual(c.nullable_int('10'), 10)
        self.assertEqual(c.nullable_int('10.0'), 10)
        self.assertEqual(c.nullable_int(''), None)
        self.assertEqual(c.nullable_int(' '), None)

    def test_nullable_string(self):
        c = Command()
        self.assertEqual(c.nullable_string('BANK'), 'BANK')
        self.assertEqual(c.nullable_string(' '), None)
        self.assertEqual(c.nullable_string(''), None)

    def test_nullable_decimal(self):
        c = Command()
        self.assertEqual(c.nullable_decimal(''), None)
        self.assertEqual(c.nullable_decimal(' '), None)
        self.assertEqual(c.nullable_decimal('12.5'), Decimal('12.5'))

    def test_nullable_float(self):
        c = Command()
        self.assertEqual(c.nullable_float(''), None)
        self.assertEqual(c.nullable_float(' '), None)
        self.assertEqual(c.nullable_float('12.5'), 12.5)

    def test_create_rate(self):
        #rate_id, product_id, region_id, lock, base_rate, total_points
        row = ['1', '12', '200', '40', '3.125', '3']

        now = datetime.now()

        c = Command()
        r = c.create_rate(row, now)
        self.assertEqual(r.rate_id, 1)
        self.assertEqual(r.product_id, 12)
        self.assertEqual(r.lock, 40)
        self.assertEqual(r.base_rate, Decimal('3.125'))
        self.assertEqual(r.data_timestamp, now)
        self.assertEqual(r.region_id, 200)
