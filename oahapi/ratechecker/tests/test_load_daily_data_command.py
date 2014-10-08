import os
import shutil
import stat
import zipfile
from mock import MagicMock, patch

from decimal import Decimal
from datetime import datetime
from django.test import TestCase
from django.db import connection, OperationalError
from django.core import mail

from ratechecker.management.commands.load_daily_data import Command, OaHException
from ratechecker.models import Product


class LoadDailyTestCase(TestCase):

    def create_test_files(self, data):
        """ Create files in test_folder for tests."""
        for key in data:
            f = file(data[key]['file'], 'w+')
            f.write('So the size is not 0')
            f.close()

    def create_product(self, row):
        """ Helper function to save a product."""
        p = Product()
        p.plan_id = int(row[0])
        p.institution = row[1]
        p.loan_purpose = row[2]
        p.pmt_type = row[3]
        p.loan_type = row[4]
        p.loan_term = int(row[5])
        p.int_adj_term = self.c.nullable_int(row[6])
        p.adj_period = self.c.nullable_int(row[7])
        p.io = self.c.string_to_boolean(row[8])
        p.arm_index = self.c.nullable_string(row[9])
        p.int_adj_cap = self.c.nullable_int(row[10])
        p.annual_cap = self.c.nullable_int(row[11])
        p.loan_cap = self.c.nullable_int(row[12])
        p.arm_margin = self.c.nullable_decimal(row[13])
        p.ai_value = self.c.nullable_decimal(row[14])
        p.min_ltv = float(row[15])
        p.max_ltv = float(row[16])
        p.min_fico = int(row[17])
        p.max_fico = int(row[18])
        p.min_loan_amt = Decimal(row[19])
        p.max_loan_amt = Decimal(row[20])
        p.data_timestamp = datetime.strptime('20140101', '%Y%m%d')
        p.save()
        return p

    def setUp(self):
        self.c = Command()
        self.test_dir = 'ratechecker/tests/test_folder'
        self.dummyargs = {
            'product': {'date': '20140101', 'file': self.test_dir + '/20140101_product.csv'},
            'adjustment': {'date': '20140101', 'file': self.test_dir + '/20140101_adjustment.csv'},
            'rate': {'date': '20140101', 'file': self.test_dir + '/20140101_rate.csv'},
            'region': {'date': '20140101', 'file': self.test_dir + '/20140101_region.csv'},
        }

        os.mkdir(self.test_dir)

    def tearDown(self):
        """ Delete the test_folder dir."""
        path = os.path.join(os.getcwd(), self.test_dir)
        shutil.rmtree(path)

    def test_string_to_boolean(self):
        b = self.c.string_to_boolean('abc')
        self.assertEqual(b, None)

        b = self.c.string_to_boolean('False')
        self.assertFalse(b)

        b = self.c.string_to_boolean('True')
        self.assertTrue(True)

    def test_nullable_int(self):
        self.assertEqual(self.c.nullable_int('10'), 10)
        self.assertEqual(self.c.nullable_int('10.0'), 10)
        self.assertEqual(self.c.nullable_int(''), None)
        self.assertEqual(self.c.nullable_int(' '), None)

    def test_nullable_string(self):
        self.assertEqual(self.c.nullable_string('BANK'), 'BANK')
        self.assertEqual(self.c.nullable_string(' '), None)
        self.assertEqual(self.c.nullable_string(''), None)

    def test_nullable_decimal(self):
        self.assertEqual(self.c.nullable_decimal(''), None)
        self.assertEqual(self.c.nullable_decimal(' '), None)
        self.assertEqual(self.c.nullable_decimal('12.5'), Decimal('12.5'))

    def test_nullable_float(self):
        self.assertEqual(self.c.nullable_float(''), None)
        self.assertEqual(self.c.nullable_float(' '), None)
        self.assertEqual(self.c.nullable_float('12.5'), 12.5)

    def test_create_rate(self):
        #rate_id, product_id, region_id, lock, base_rate, total_points
        row = ['1', '12', '200', '40', '3.125', '3']

        now = datetime.now()
        r = self.c.create_rate(row, now)
        self.assertEqual(r.rate_id, 1)
        self.assertEqual(r.product_id, 12)
        self.assertEqual(r.lock, 40)
        self.assertEqual(r.base_rate, Decimal('3.125'))
        self.assertEqual(r.data_timestamp, now)
        self.assertEqual(r.region_id, 200)

    def test_delete_temp_tables(self):
        """ ...  some exist, others - not."""
        # don't know how to easily test table (in)existence
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE temporary_product(a TEXT)')
        self.assertRaises(OperationalError, cursor.execute, 'SELECT * FROM temporary_region')
        empty = cursor.execute('SELECT * FROM temporary_product')
        self.assertTrue(empty is not None)
        self.c.delete_temp_tables(cursor)
        self.assertRaises(OperationalError, cursor.execute, 'SELECT * FROM temporary_product')

    @patch('ratechecker.management.commands.load_daily_data.Command.load_region_data')
    @patch('ratechecker.management.commands.load_daily_data.Command.load_rate_data')
    @patch('ratechecker.management.commands.load_daily_data.Command.load_adjustment_data')
    @patch('ratechecker.management.commands.load_daily_data.Command.load_product_data')
    @patch('ratechecker.management.commands.load_daily_data.Command.reload_old_data')
    def test_load_new_data(self, mock1, mock2, mock3, mock4, mock5):
        """ ... as simple as they come."""
        mock1.side_effect = lambda k: True
        mock2.side_effect = lambda data, path: True
        mock3.side_effect = lambda data, path: False
        mock4.side_effect = lambda data, path: True
        mock5.side_effect = lambda data, path: True
        self.assertRaises(OaHException, self.c.load_new_data, self.dummyargs, None)

        mock3.side_effect = lambda data, path: True
        result = self.c.load_new_data(self.dummyargs, None)
        self.assertTrue(not result)

    def test_email_status(self):
        """ ... """
        self.c.status = 1
        self.c.email_status(self.dummyargs)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('Success' in mail.outbox[0].subject)

        self.c.status = 0
        self.c.message = 'Additional error message'
        self.c.email_status(self.dummyargs)
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue('Failed' in mail.outbox[1].subject)
        self.assertTrue('Additional error message' in mail.outbox[1].body)

    def test_reload_old_data(self):
        """ .. and archive_data_to_temp_tables, delete_temp_tables, delete_data_from_base_tables """
        cursor = connection.cursor()
        row = [
            '5999', 'SMPL', 'PURCH', 'ARM', 'JUMBO', '30', '7.0', '1',
            'False', 'LIBOR', '5.0000', '2.0000', '5.0000', '2.5000',
            '.5532', '1', '90', '620', '850', '417001', '2000000', 1, 1, 0
        ]
        # Original product object
        op = self.create_product(row)

        self.c.archive_data_to_temp_tables(cursor)

        result = cursor.execute('SELECT * FROM temporary_product')
        self.assertTrue(len(result.fetchall()) == 1)
        result = Product.objects.all()
        self.assertFalse(result)

        self.c.reload_old_data(cursor)
        result = Product.objects.all()
        self.assertEqual(len(result), 1)
        self.assertTrue(op == result[0])

    def test_delete_data_files(self):
        """ Should work till the end of times."""
        self.create_test_files(self.dummyargs)
        result = os.listdir(self.test_dir)
        self.assertTrue(result)
        self.c.delete_data_files(self.dummyargs)
        result = os.listdir(self.test_dir)
        self.assertFalse(result)

    def test__check_files__empty(self):
        """ with [] and None as arg."""
        self.assertRaises(OaHException, self.c._check_files, [])
        self.assertRaises(TypeError, self.c._check_files, None)

    def test__check_files__valid(self):
        """ .. with a valid arg."""
        args = {
            'a': {'date': '20140301', 'data': 'product', 'file': self.test_dir + '/20140301_product.csv'},
            'b': {'date': '20140301', 'data': 'adjustment', 'file': self.test_dir + '/20140301_adjustment.csv'},
            'c': {'date': '20140301', 'data': 'rate', 'file': self.test_dir + '/20140301_rate.csv'},
            'd': {'date': '20140301', 'data': 'region', 'file': self.test_dir + '/20140301_region.csv'},
            'e': {'date': '20140201', 'data': 'product', 'file': self.test_dir + '/20140301_product.csv'},
            'f': {'date': '20140201', 'data': 'adjustment', 'file': self.test_dir + '/20140301_adjustment.csv'},
            'g': {'date': '20140201', 'data': 'rate', 'file': self.test_dir + '/20140301_rate.csv'},
            'h': {'date': '20140201', 'data': 'region', 'file': self.test_dir + '/20140301_region.csv'},
        }
        result = self.c._check_files([args[key] for key in args])
        self.assertEqual(len(result), 4)
        self.assertEqual('20140301', result['product']['date'])
        del args['c']
        result = self.c._check_files([args[key] for key in args])
        self.assertEqual(len(result), 4)
        self.assertTrue('20140201', result['product']['date'])
        del args['e']
        self.assertRaises(OaHException, self.c._check_files, [args[key] for key in args])

    def test__check_file__bad_name(self):
        """ ... invalid filename """
        result = self.c._check_file('Bad_name', '')
        self.assertFalse(result)
        result = self.c._check_file('product_20140301.csv', '')
        self.assertFalse(result)
        result = self.c._check_file('2014.03.01-prodcut.txt', '')
        self.assertFalse(result)
        result = self.c._check_file('20140301_product.txt', '')
        self.assertFalse(result)

    def test__check_file__empty_file(self):
        """ ... an empty file"""
        file(self.test_dir + '/20140301_product.csv', 'w')
        result = os.listdir(self.test_dir)
        self.assertTrue(result)
        root_folder = os.path.join(os.getcwd(), self.test_dir)
        result = self.c._check_file('20140301_product.csv', root_folder)
        self.assertFalse(result)

    def test__check_file__not_readable(self):
        """ ... not readable file."""
        path = self.test_dir + '/20140301_product.csv'
        f = file(path, 'w')
        f.write('Simple text')
        f.close()
        os.chmod(path, stat.S_IWRITE)
        root_folder = os.path.join(os.getcwd(), self.test_dir)
        result = self.c._check_file('20140301_product.csv', root_folder)
        self.assertFalse(result)

    def test__check_file__valid(self):
        path = self.test_dir + '/20140303_rate.csv'
        f = file(path, 'w')
        f.write('Sample text')
        f.close()
        root_folder = os.path.join(os.getcwd(), self.test_dir)
        result = self.c._check_file('20140303_rate.csv', root_folder)
        self.assertTrue('date' in result)
        self.assertEqual(result['data'], 'rate')
        self.assertEqual(result['file'], os.path.join(root_folder, '20140303_rate.csv'))

    def test_read_filenames(self):
        """ ... """
        pass

    def test_unzip_datafiles(self):
        """ ... see that files are getting extracted correctly."""
        with open(self.test_dir + '/20130101.zip', 'w') as fh:
            fh.write('This is not a zip file.')
        tfile_path = self.test_dir + '/TextFile.txt'
        zfile_path = self.test_dir + '/20130102_A.zip'
        with open(tfile_path, 'w') as fh:
            fh.write('This is a simple text file.')
        zf = zipfile.ZipFile(zfile_path, mode='w')
        zf.write(tfile_path)
        zf.close()
        os.remove(tfile_path)
        zf = zipfile.ZipFile(zfile_path)

        self.assertFalse(os.path.exists(tfile_path))
        self.assertTrue(tfile_path in zf.namelist())
        data = zf.read(tfile_path)
        self.assertEqual(data, 'This is a simple text file.')

        self.c.unzip_datafiles(self.test_dir)
        self.assertFalse(os.path.exists(tfile_path))

        os.rename(zfile_path, zfile_path[0:-6] + '.zip')
        self.c.unzip_datafiles(self.test_dir)
        self.assertTrue(os.path.exists(tfile_path))
