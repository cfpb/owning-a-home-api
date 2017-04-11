import argparse
import os
import shutil
import tempfile

from decimal import Decimal
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from mock import patch

from ratechecker.management.commands.load_daily_data import (
    Command, latest_archive
)


class TestLatestArchive(TestCase):
    def test_get_latest_archive_no_files(self):
        with patch('os.listdir', return_value=[]):
            with self.assertRaises(argparse.ArgumentTypeError):
                latest_archive('path')

    def test_get_latest_archive_no_matching_files(self):
        files = ['a.zip', 'b.txt']
        with patch('os.listdir', return_value=files):
            with self.assertRaises(argparse.ArgumentTypeError):
                latest_archive('path')

    def test_get_latest_archive_single_matching_file(self):
        files = ['a.zip', '20170201.zip']
        with patch('os.listdir', return_value=files):
            self.assertEqual(latest_archive('path'), 'path/20170201.zip')

    def test_get_latest_archive_multiple_files(self):
        files = ['20170202.zip', '20170203.zip', '20170201.zip']
        with patch('os.listdir', return_value=files):
            self.assertEqual(latest_archive('path'), 'path/20170203.zip')


class LoadDailyTestCase(TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def touch_file(self, f):
        with open(f, 'a'):
            os.utime(f, None)

    def test_run_command_no_arguments(self):
        with self.assertRaises(CommandError):
            call_command('load_daily_data', verbosity=0)

    def test_run_command_invalid_data_dir(self):
        with self.assertRaises(CommandError):
            call_command('load_daily_data', 'invalid-path', verbosity=0)

    def test_run_command_invalid_scenario_file(self):
        with self.assertRaises(CommandError):
            call_command(
                'load_daily_data',
                self.tempdir,
                validation_scenario_file='invalid.jsonl',
                verbosity=0
            )

    def test_run_command_load_called(self):
        archive_filename = os.path.join(self.tempdir, '20170101.zip')
        self.touch_file(archive_filename)
        with patch(
            (
                'ratechecker.management.commands.load_daily_data.'
                'Command.load_archive_data'
            )
        ) as load:
            call_command('load_daily_data', self.tempdir, verbosity=0)
            load.assert_called_once_with(archive_filename)

    def test_string_to_boolean_text(self):
        self.assertIsNone(Command.string_to_boolean('abc'))

    def test_string_to_boolean_false(self):
        self.assertFalse(Command.string_to_boolean('False'))

    def test_string_to_boolean_true(self):
        self.assertTrue(Command.string_to_boolean('True'))

    def test_string_to_boolean_0(self):
        self.assertFalse(Command.string_to_boolean('0'))

    def test_string_to_boolean_1(self):
        self.assertTrue(Command.string_to_boolean('1'))

    def test_nullable_int_integer(self):
        self.assertEqual(Command.nullable_int('10'), 10)

    def test_nullable_int_float(self):
        self.assertEqual(Command.nullable_int('10.0'), 10)

    def test_nullable_int_empty_string(self):
        self.assertIsNone(Command.nullable_int(''))

    def test_nullable_int_space(self):
        self.assertIsNone(Command.nullable_int(' '))

    def test_nullable_string_text(self):
        self.assertEqual(Command.nullable_string('BANK'), 'BANK')

    def test_nullable_string_empty_string(self):
        self.assertIsNone(Command.nullable_string(''))

    def test_nullable_string_space(self):
        self.assertIsNone(Command.nullable_string(' '))

    def test_nullable_decimal_decimal(self):
        self.assertEqual(Command.nullable_decimal('12.5'), Decimal('12.500'))

    def test_nullable_decimal_empty_string(self):
        self.assertIsNone(Command.nullable_decimal(''))

    def test_nullable_decimal_space(self):
        self.assertIsNone(Command.nullable_decimal(' '))
