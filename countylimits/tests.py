import os
import unittest

import mock
from mock import mock_open, patch
from rest_framework import status

from django.test import TestCase
from django.utils.six import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError

from countylimits.models import CountyLimit, County, State
from countylimits.management.commands import load_county_limits
from countylimits.data_collection.county_data_monitor import (
    check_for_county_changes,
    store_change_log,
    get_current_log,
    get_base_log,
    get_lines)


try:
    BASE_PATH = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))) + '/'
except:  # pragma: no cover
    BASE_PATH = ''


class CheckCountyChangesCommand(unittest.TestCase):

    def setUp(self):
        stdout_patch = mock.patch('sys.stdout')
        stdout_patch.start()
        self.addCleanup(stdout_patch.stop)

    @mock.patch(
        'countylimits.management.commands.oah_check_county_changes.'
        'check_for_county_changes')
    def test_check_county_without_email(self, mock_check):
        mock_check.return_value = 'OK'
        call_command('oah_check_county_changes')
        self.assertEqual(mock_check.call_count, 1)

    @mock.patch(
        'countylimits.management.commands.oah_check_county_changes.'
        'check_for_county_changes')
    def test_check_county_with_email(self, mock_check):
        mock_check.return_value = 'Emails were sent'
        call_command('oah_check_county_changes', '--email', 'fake@example.com')
        self.assertEqual(mock_check.call_count, 1)


class DataCollectionTest(unittest.TestCase):
    """Test data automation functions"""

    def test_get_lines(self):
        lines_in = "\n\nline 1\nline 2\n\n\nline 3\n\n"
        expected_result = ['line 1', 'line 2', 'line 3']
        lines_out = get_lines(lines_in)
        self.assertEqual(lines_out, expected_result)

    def test_get_base_log(self):
        text = get_base_log()
        self.assertIn('2010', text)

    def test_store_changelog(self):
        m = mock_open()
        with patch("__builtin__.open", m, create=True):
            store_change_log('fake log text')
        self.assertTrue(m.call_count == 1)

    @mock.patch('countylimits.data_collection.county_data_monitor'
                '.requests.get')
    @mock.patch('countylimits.data_collection.county_data_monitor.bs')
    def test_get_current_log(self, mock_bs, mock_requests):
        get_current_log()
        self.assertEqual(mock_bs.call_count, 1)
        self.assertEqual(mock_requests.call_count, 1)

    @mock.patch(
        'countylimits.data_collection.county_data_monitor.get_current_log')
    @mock.patch(
        'countylimits.data_collection.county_data_monitor.get_base_log')
    def test_county_data_monitor_no_change(self, mock_base, mock_current):
        with open("{}/countylimits/data_collection/"
                  "changelog_2017.html".format(BASE_PATH)) as f:
            mock_base.return_value = mock_current.return_value = f.read()
        self.assertIn(
            'No county changes found',
            check_for_county_changes())

    @mock.patch(
        'countylimits.data_collection.county_data_monitor.get_current_log')
    @mock.patch(
        'countylimits.data_collection.county_data_monitor.get_base_log')
    @mock.patch(
        'countylimits.data_collection.county_data_monitor.store_change_log')
    def test_county_data_monitor_with_change_no_email(
            self, mock_store_log, mock_base, mock_current):
        with open("{}/countylimits/data_collection/"
                  "changelog_2017.html".format(BASE_PATH)) as f:
            mock_base.return_value = f.read()
            mock_current.return_value = (
                mock_base.return_value + 'When dolphins fly.\n')
        self.assertIn(
            'When dolphins fly',
            check_for_county_changes())
        self.assertEqual(mock_current.call_count, 1)
        self.assertEqual(mock_base.call_count, 1)
        self.assertEqual(mock_store_log.call_count, 1)

    @mock.patch(
        'countylimits.data_collection.county_data_monitor.get_current_log')
    @mock.patch(
        'countylimits.data_collection.county_data_monitor.get_base_log')
    @mock.patch(
        'countylimits.data_collection.county_data_monitor.send_mail')
    @mock.patch(
        'countylimits.data_collection.county_data_monitor.store_change_log')
    def test_county_data_monitor_with_change_and_email(
            self, mock_store_log, mock_mail, mock_base, mock_current):
        with open("{}/countylimits/data_collection/"
                  "changelog_2017.html".format(BASE_PATH)) as f:
            mock_base.return_value = f.read()
            mock_current.return_value = (
                mock_base.return_value + 'When dolphins fly.\n')
        msg = check_for_county_changes(email='fakemail@example.com')
        self.assertIn('When dolphins fly', msg)
        self.assertEqual(mock_mail.call_count, 1)
        self.assertEqual(mock_current.call_count, 1)
        self.assertEqual(mock_base.call_count, 1)
        self.assertEqual(mock_store_log.call_count, 1)


class CountyLimitTest(TestCase):

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

    c = load_county_limits.Command()
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
