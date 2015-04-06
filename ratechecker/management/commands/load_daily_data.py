import os
import sys
import re
import zipfile
import StringIO
import contextlib
from datetime import datetime
from csv import reader
from decimal import Decimal
from operator import itemgetter

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import warnings
import _mysql_exceptions

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from django.db.utils import OperationalError, IntegrityError

from ratechecker.models import Product, Adjustment, Region, Rate
from ratechecker.views import get_rates
from ratechecker.ratechecker_parameters import RateCheckerParameters

ARCHIVE_PATTERN = '^\d{8}\.zip$'


class OaHException(Exception):
    pass


class Command(BaseCommand):
    args = "<directory_path>"
    help = """ Loads daily interest rate data from a zip archive with CSV files. """
    messages = []
    status = 1     # 1 = FAILURE, 0 = SUCCESS

    test_scenarios = {
        '1': {'maxfico': 640, 'lock': 60, 'rate_structure': 'Fixed', 'price': 150000,
                'loan_amount': 150000, 'arm_type': '', 'io': '', 'institution': 'BOFA',
                'loan_type': 'VA', 'ltv': 100, 'property_type': '', 'state': 'AK', 'minfico': 640,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '2': {'maxfico': 690, 'lock': 30, 'rate_structure': 'Fixed', 'price': 210526,
                'loan_amount': 200000, 'arm_type': '', 'io': '', 'institution': 'COMPASS',
                'loan_type': 'VA', 'ltv': 95, 'property_type': '', 'state': 'AL', 'minfico': 690,
                'loan_term': 15, 'loan_purpose': 'REFI'},
        '3': {'maxfico': 710, 'lock': 45, 'rate_structure': 'ARM', 'price': 83333,
                'loan_amount': 75000, 'arm_type': '3-1', 'io': '', 'institution': 'PNC',
                'loan_type': 'CONF', 'ltv': 90, 'property_type': '', 'state': 'AR', 'minfico': 710,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '4': {'maxfico': 745, 'lock': 60, 'rate_structure': 'ARM', 'price': 444444,
                'loan_amount': 400000, 'arm_type': '3-1', 'io': 1.0, 'institution': 'USBANK',
                'loan_type': 'CONF', 'ltv': 90, 'property_type': '', 'state': 'AZ', 'minfico': 745,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '5': {'maxfico': 760, 'lock': 30, 'rate_structure': 'Fixed', 'price': 1125000,
                'loan_amount': 900000, 'arm_type': '', 'io': '', 'institution': 'UNBK',
                'loan_type': 'JUMBO', 'ltv': 80, 'property_type': '', 'state': 'CA', 'minfico': 760,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '6': {'maxfico': 740, 'lock': 45, 'rate_structure': 'Fixed', 'price': 411764,
                'loan_amount': 350000, 'arm_type': '', 'io': '', 'institution': 'PATELCO',
                'loan_type': 'CONF', 'ltv': 85, 'property_type': '', 'state': 'CA', 'minfico': 740,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '7': {'maxfico': 780, 'lock': 60, 'rate_structure': 'Fixed', 'price': 2000000,
                'loan_amount': 1500000, 'arm_type': '', 'io': '', 'institution': 'FIRSTBANK',
                'loan_type': 'JUMBO', 'ltv': 75, 'property_type': '', 'state': 'CO', 'minfico': 780,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '8': {'maxfico': 715, 'lock': 30, 'rate_structure': 'ARM', 'price': 617647,
                'loan_amount': 525000, 'arm_type': '7-1', 'io': 1.0, 'institution': 'RBS',
                'loan_type': 'AGENCY', 'ltv': 85, 'property_type': '', 'state': 'CT', 'minfico': 715,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '9': {'maxfico': 660, 'lock': 45, 'rate_structure': 'Fixed', 'price': 631578,
                'loan_amount': 600000, 'arm_type': '', 'io': '', 'institution': 'QUICKEN',
                'loan_type': 'FHA-HB', 'ltv': 95, 'property_type': '', 'state': 'DC', 'minfico': 660,
                'loan_term': 15, 'loan_purpose': 'PURCH'},
        '10': {'maxfico': 690, 'lock': 60, 'rate_structure': 'Fixed', 'price': 233333,
                'loan_amount': 175000, 'arm_type': '', 'io': '', 'institution': 'CAPITAL ONE',
                'loan_type': 'CONF', 'ltv': 75, 'property_type': '', 'state': 'DE', 'minfico': 690,
                'loan_term': 15, 'loan_purpose': 'REFI'},
        '11': {'maxfico': 780, 'lock': 30, 'rate_structure': 'Fixed', 'price': 305555,
                'loan_amount': 275000, 'arm_type': '', 'io': '', 'institution': 'KINECTA',
                'loan_type': 'CONF', 'ltv': 90, 'property_type': '', 'state': 'FL', 'minfico': 780,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '12': {'maxfico': 800, 'lock': 45, 'rate_structure': 'ARM', 'price': 1000000,
                'loan_amount': 700000, 'arm_type': '3-1', 'io': '', 'institution': 'FIRST TECH FCU',
                'loan_type': 'JUMBO', 'ltv': 70, 'property_type': '', 'state': 'GA', 'minfico': 800,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '13': {'maxfico': 720, 'lock': 60, 'rate_structure': 'Fixed', 'price': 823529,
                'loan_amount': 700000, 'arm_type': '', 'io': '', 'institution': 'PNC',
                'loan_type': 'AGENCY', 'ltv': 85, 'property_type': '', 'state': 'HI', 'minfico': 720,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '14': {'maxfico': 680, 'lock': 30, 'rate_structure': 'ARM', 'price': 222222,
                'loan_amount': 200000, 'arm_type': '5-1', 'io': '', 'institution': '53RD',
                'loan_type': 'CONF', 'ltv': 90, 'property_type': '', 'state': 'IA', 'minfico': 680,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '15': {'maxfico': 650, 'lock': 45, 'rate_structure': 'Fixed', 'price': 105263,
                'loan_amount': 100000, 'arm_type': '', 'io': '', 'institution': 'ZIONS',
                'loan_type': 'FHA', 'ltv': 95, 'property_type': '', 'state': 'ID', 'minfico': 650,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '16': {'maxfico': 690, 'lock': 60, 'rate_structure': 'Fixed', 'price': 750000,
                'loan_amount': 600000, 'arm_type': '', 'io': '', 'institution': 'ASTORIA',
                'loan_type': 'AGENCY', 'ltv': 80, 'property_type': 'CONDO', 'state': 'IL', 'minfico': 690,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '17': {'maxfico': 710, 'lock': 30, 'rate_structure': 'Fixed', 'price': 157894,
                'loan_amount': 150000, 'arm_type': '', 'io': '', 'institution': 'CITI',
                'loan_type': 'FHA', 'ltv': 95, 'property_type': '', 'state': 'IN', 'minfico': 710,
                'loan_term': 15, 'loan_purpose': 'PURCH'},
        '18': {'maxfico': 760, 'lock': 45, 'rate_structure': 'Fixed', 'price': 277777,
                'loan_amount': 250000, 'arm_type': '', 'io': '', 'institution': 'BECU',
                'loan_type': 'CONF', 'ltv': 90, 'property_type': '', 'state': 'KS', 'minfico': 760,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '19': {'maxfico': 715, 'lock': 60, 'rate_structure': 'Fixed', 'price': 200000,
                'loan_amount': 150000, 'arm_type': '', 'io': '', 'institution': '53RD',
                'loan_type': 'VA', 'ltv': 75, 'property_type': '', 'state': 'KY', 'minfico': 715,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '20': {'maxfico': 695, 'lock': 30, 'rate_structure': 'ARM', 'price': 107526,
                'loan_amount': 100000, 'arm_type': '5-1', 'io': '', 'institution': 'REGIONS',
                'loan_type': 'CONF', 'ltv': 93, 'property_type': '', 'state': 'LA', 'minfico': 695,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '21': {'maxfico': 765, 'lock': 45, 'rate_structure': 'ARM', 'price': 533333,
                'loan_amount': 400000, 'arm_type': '10-1', 'io': '', 'institution': 'WEBSTER',
                'loan_type': 'CONF', 'ltv': 75, 'property_type': 'CONDO', 'state': 'MA',
                'minfico': 765, 'loan_term': 30, 'loan_purpose': 'REFI'},
        '22': {'maxfico': 780, 'lock': 60, 'rate_structure': 'ARM', 'price': 687500,
                'loan_amount': 550000, 'arm_type': '7-1', 'io': '', 'institution': 'TDBANK',
                'loan_type': 'AGENCY', 'ltv': 80, 'property_type': '', 'state': 'MD', 'minfico': 780,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '23': {'maxfico': 750, 'lock': 30, 'rate_structure': 'Fixed', 'price': 171428,
                'loan_amount': 120000, 'arm_type': '', 'io': '', 'institution': 'TDBANK',
                'loan_type': 'CONF', 'ltv': 70, 'property_type': '', 'state': 'ME', 'minfico': 750,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '24': {'maxfico': 680, 'lock': 45, 'rate_structure': 'Fixed', 'price': 225000,
                'loan_amount': 180000, 'arm_type': '', 'io': '', 'institution': 'HSBC',
                'loan_type': 'FHA', 'ltv': 80, 'property_type': '', 'state': 'MI', 'minfico': 680,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '25': {'maxfico': 790, 'lock': 60, 'rate_structure': 'ARM', 'price': 470588,
                'loan_amount': 400000, 'arm_type': '10-1', 'io': '',
                 'institution': 'CHSCHWAB', 'loan_type': 'CONF', 'ltv': 85,
                 'property_type': '', 'state': 'MN', 'minfico': 790, 'loan_term': 30,
                 'loan_purpose': 'REFI'},
        '26': {'maxfico': 710, 'lock': 30, 'rate_structure': 'Fixed', 'price': 166666,
                'loan_amount': 150000, 'arm_type': '', 'io': '', 'institution': 'HARRIS',
                'loan_type': 'FHA', 'ltv': 90, 'property_type': '', 'state': 'MO', 'minfico': 710,
                'loan_term': 15, 'loan_purpose': 'PURCH'},
        '27': {'maxfico': 705, 'lock': 45, 'rate_structure': 'Fixed', 'price': 100000,
                'loan_amount': 80000, 'arm_type': '', 'io': '', 'institution': 'PNC',
                'loan_type': 'CONF', 'ltv': 80, 'property_type': '', 'state': 'MS', 'minfico': 705,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '28': {'maxfico': 740, 'lock': 60, 'rate_structure': 'ARM', 'price': 470588,
                'loan_amount': 400000, 'arm_type': '5-1', 'io': '', 'institution': 'STATEFARM',
                'loan_type': 'CONF', 'ltv': 85, 'property_type': '', 'state': 'MT', 'minfico': 740,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '29': {'maxfico': 690, 'lock': 30, 'rate_structure': 'Fixed', 'price': 368421,
                'loan_amount': 350000, 'arm_type': '', 'io': '', 'institution': 'JPM',
                'loan_type': 'FHA-HB', 'ltv': 95, 'property_type': 'CONDO', 'state': 'NC',
                'minfico': 690, 'loan_term': 30, 'loan_purpose': 'PURCH'},
        '30': {'maxfico': 705, 'lock': 45, 'rate_structure': 'Fixed', 'price': 125625,
                'loan_amount': 100500, 'arm_type': '', 'io': '', 'institution': 'STATEFARM',
                'loan_type': 'CONF', 'ltv': 80, 'property_type': '', 'state': 'ND', 'minfico': 705,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '31': {'maxfico': 710, 'lock': 60, 'rate_structure': 'Fixed', 'price': 259067.35751295337,
                'loan_amount': 250000, 'arm_type': '', 'io': '', 'institution': 'BOFA',
                'loan_type': 'FHA', 'ltv': 96.5, 'property_type': '', 'state': 'NE', 'minfico': 710,
                'loan_term': 15, 'loan_purpose': 'REFI'},
        '32': {'maxfico': 740, 'lock': 30, 'rate_structure': 'Fixed', 'price': 421052,
                'loan_amount': 400000, 'arm_type': '', 'io': '', 'institution': 'SANTANDER',
                'loan_type': 'FHA-HB', 'ltv': 95, 'property_type': '', 'state': 'NH', 'minfico': 740,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '33': {'maxfico': 680, 'lock': 45, 'rate_structure': 'Fixed', 'price': 450000,
                'loan_amount': 450000, 'arm_type': '', 'io': '', 'institution': 'CITI',
                'loan_type': 'VA-HB', 'ltv': 100, 'property_type': '', 'state': 'NJ', 'minfico': 680,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '34': {'maxfico': 720, 'lock': 60, 'rate_structure': 'ARM', 'price': 294117,
                'loan_amount': 250000, 'arm_type': '3-1', 'io': '', 'institution': 'STATEFARM',
                'loan_type': 'CONF', 'ltv': 85, 'property_type': '', 'state': 'NM', 'minfico': 720,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '35': {'maxfico': 745, 'lock': 30, 'rate_structure': 'ARM', 'price': 502409,
                'loan_amount': 417000, 'arm_type': '7-1', 'io': '', 'institution': 'ZIONS',
                'loan_type': 'CONF', 'ltv': 83, 'property_type': '', 'state': 'NV', 'minfico': 745,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '36': {'maxfico': 695, 'lock': 45, 'rate_structure': 'Fixed', 'price': 500000,
                'loan_amount': 400000, 'arm_type': '', 'io': '', 'institution': 'WELLS',
                'loan_type': 'CONF', 'ltv': 80, 'property_type': 'COOP', 'state': 'NY', 'minfico': 695,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '37': {'maxfico': 710, 'lock': 60, 'rate_structure': 'Fixed', 'price': 204081.63265306121,
                'loan_amount': 200000, 'arm_type': '', 'io': '', 'institution': 'HUNTINGTON',
                'loan_type': 'VA', 'ltv': 98.0, 'property_type': '', 'state': 'OH', 'minfico': 710,
                'loan_term': 15, 'loan_purpose': 'PURCH'},
        '38': {'maxfico': 650, 'lock': 30, 'rate_structure': 'Fixed', 'price': 55555,
                'loan_amount': 50000, 'arm_type': '', 'io': '', 'institution': 'JPM',
                'loan_type': 'FHA', 'ltv': 90, 'property_type': '', 'state': 'OK', 'minfico': 650,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '39': {'maxfico': 730, 'lock': 45, 'rate_structure': 'ARM', 'price': 157894,
                'loan_amount': 150000, 'arm_type': '5-1', 'io': '', 'institution': 'ONPOINT',
                'loan_type': 'CONF', 'ltv': 95, 'property_type': '', 'state': 'OR', 'minfico': 730,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '40': {'maxfico': 725, 'lock': 60, 'rate_structure': 'Fixed', 'price': 294117,
                'loan_amount': 250000, 'arm_type': '', 'io': '', 'institution': 'FIRSTNIAGARA',
                'loan_type': 'FHA', 'ltv': 85, 'property_type': '', 'state': 'PA', 'minfico': 725,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '41': {'maxfico': 690, 'lock': 30, 'rate_structure': 'Fixed', 'price': 315789,
                'loan_amount': 300000, 'arm_type': '', 'io': '', 'institution': 'CHSCHWAB',
                'loan_type': 'FHA-HB', 'ltv': 95, 'property_type': '', 'state': 'RI', 'minfico': 690,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '42': {'maxfico': 780, 'lock': 45, 'rate_structure': 'Fixed', 'price': 750000,
                'loan_amount': 600000, 'arm_type': '', 'io': '', 'institution': 'CAPITAL ONE',
                'loan_type': 'AGENCY', 'ltv': 80, 'property_type': '', 'state': 'SC', 'minfico': 780,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '43': {'maxfico': 750, 'lock': 60, 'rate_structure': 'Fixed', 'price': 66666,
                'loan_amount': 60000, 'arm_type': '', 'io': '', 'institution': 'STATEFARM',
                'loan_type': 'CONF', 'ltv': 90, 'property_type': '', 'state': 'SD', 'minfico': 750,
                'loan_term': 15, 'loan_purpose': 'PURCH'},
        '44': {'maxfico': 630, 'lock': 30, 'rate_structure': 'Fixed', 'price': 63157,
                'loan_amount': 60000, 'arm_type': '', 'io': '', 'institution': 'RBS',
                'loan_type': 'FHA', 'ltv': 95, 'property_type': '', 'state': 'TN', 'minfico': 630,
                'loan_term': 15, 'loan_purpose': 'PURCH'},
        '45': {'maxfico': 680, 'lock': 45, 'rate_structure': 'Fixed', 'price': 263157,
                'loan_amount': 250000, 'arm_type': '', 'io': '', 'institution': 'REGIONS',
                'loan_type': 'FHA', 'ltv': 95, 'property_type': '', 'state': 'TX', 'minfico': 680,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '46': {'maxfico': 780, 'lock': 60, 'rate_structure': 'Fixed', 'price': 566666,
                'loan_amount': 425000, 'arm_type': '', 'io': '', 'institution': 'KINECTA',
                'loan_type': 'JUMBO', 'ltv': 75, 'property_type': '', 'state': 'UT', 'minfico': 780,
                'loan_term': 15, 'loan_purpose': 'PURCH'},
        '47': {'maxfico': 710, 'lock': 30, 'rate_structure': 'Fixed', 'price': 605263,
                'loan_amount': 575000, 'arm_type': '', 'io': '', 'institution': 'HSBC',
                'loan_type': 'VA-HB', 'ltv': 95, 'property_type': '', 'state': 'VA', 'minfico': 710,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '48': {'maxfico': 740, 'lock': 45, 'rate_structure': 'Fixed', 'price': 1000000,
                'loan_amount': 800000, 'arm_type': '', 'io': '', 'institution': 'QUICKEN',
                'loan_type': 'JUMBO', 'ltv': 80, 'property_type': '', 'state': 'VT', 'minfico': 740,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '49': {'maxfico': 705, 'lock': 60, 'rate_structure': 'Fixed', 'price': 277777,
                'loan_amount': 250000, 'arm_type': '', 'io': '', 'institution': 'FIRST FEDERAL',
                'loan_type': 'VA', 'ltv': 90, 'property_type': '', 'state': 'WA', 'minfico': 705,
                'loan_term': 15, 'loan_purpose': 'REFI'},
        '50': {'maxfico': 750, 'lock': 30, 'rate_structure': 'ARM', 'price': 368421,
                'loan_amount': 350000, 'arm_type': '10-1', 'io': '', 'institution': 'HARRIS',
                'loan_type': 'CONF', 'ltv': 95, 'property_type': '', 'state': 'WI', 'minfico': 750,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '51': {'maxfico': 790, 'lock': 45, 'rate_structure': 'ARM', 'price': 687500,
                'loan_amount': 550000, 'arm_type': '10-1', 'io': 1.0, 'institution': 'USBANK',
                'loan_type': 'AGENCY', 'ltv': 80, 'property_type': '', 'state': 'WV', 'minfico': 790,
                'loan_term': 30, 'loan_purpose': 'REFI'},
        '52': {'maxfico': 750, 'lock': 60, 'rate_structure': 'ARM', 'price': 588235,
                'loan_amount': 500000, 'arm_type': '5-1', 'io': 1.0, 'institution': 'PNC',
                'loan_type': 'JUMBO', 'ltv': 85, 'property_type': '', 'state': 'WY', 'minfico': 750,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '53': {'maxfico': 740, 'lock': 60, 'rate_structure': 'ARM', 'price': 285714,
                'loan_amount': 200000, 'arm_type': '5-1', 'io': '', 'institution': 'WELLS',
                'loan_type': 'CONF', 'ltv': 70, 'property_type': '', 'state': 'CA', 'minfico': 740,
                'loan_term': 30, 'loan_purpose': 'PURCH'},
        '54': {'maxfico': 740, 'lock': 60, 'rate_structure': 'Fixed', 'price': 250000,
                'loan_amount': 200000, 'arm_type': '', 'io': '', 'institution': 'BOFA',
                'loan_type': 'CONF', 'ltv': 80, 'property_type': '', 'state': 'CA', 'minfico': 740,
                'loan_term': 30, 'loan_purpose': 'PURCH'}
    }

    def handle(self, *args, **options):
        # Get rid of runtime errors caused by MySQL warnings for IF EXISTS query
        warnings.filterwarnings('ignore', category=_mysql_exceptions.Warning)

        try:
            src_dir = args[0]
            self.messages.append('Command run with the following args: %s' % args)

            cursor = connection.cursor()
            sorted_arch_list = self.arch_list(src_dir)
            self.archive_data_to_temp_tables(cursor)
            for arch in sorted_arch_list:
                self.messages.append('Processing <%s>' % arch)
                self.delete_data_from_base_tables()
                try:
                    with contextlib.closing(zipfile.ZipFile(arch)) as zf:
                        self.load_arch_data(zf)
                        precalculated_results = self.get_precalculated_results(zf)
                        self.compare_scenarios_output(precalculated_results)
                    self.messages.append('Successfully loaded data from <%s>' % arch)
                    self.status = 0
                    break
                except zipfile.BadZipfile as e:
                    self.messages.append(' Warning: %s.' % e)
                except OaHException as e:
                    self.messages.append(' Warning: %s.' % e)
                except ValueError as e:
                    self.messages.append(' Warning: %s.' % e)
                except IntegrityError as e:
                    self.messages.append(' Warning: %s.' % e)
                except KeyError as e:
                    self.messages.append(' Warning: %s.' % e)

            if self.status:
                self.messages.append('Warning: reloading "yesterday" data')
                self.delete_data_from_base_tables()
                self.reload_old_data(cursor)

            self.delete_temp_tables(cursor)
        except IndexError as e:
            self.messages.append('Error: %s. Has a source directory been provided?' % e)
        except OSError as e:
            self.messages.append('Error: %s.' % e)
        except OperationalError as e:
            self.messages.append('Error: %s.' % e)

        self.output_messages()
        sys.exit(self.status)

    def arch_list(self, folder):
        """ Return list of archives of the YYYYMMDD.zip form."""
        archives = [os.path.join(folder, name) for name in os.listdir(folder)
                    if re.match(ARCHIVE_PATTERN, name)]
        return sorted(archives, reverse=True)

    def load_arch_data(self, zipfile):
        """ Load data from zipfile."""
        date = zipfile.filename[:-4]
        date = date.split('/')[-1]
        self.load_product_data(date, zipfile)
        self.load_adjustment_data(date, zipfile)
        self.load_rate_data(date, zipfile)
        self.load_region_data(date, zipfile)

    def string_to_boolean(self, bstr):
        """ If bstr is 'True' return True. If bstr is 'False' return False.
        Otherwise return None. This is case-insensitive.  """

        if bstr.lower() == 'true' or bstr == '1':
            return True
        elif bstr.lower() == 'false' or bstr == '0':
            return False

    def nullable_int(self, row_item):
        if row_item.strip():
            try:
                return int(row_item)
            except ValueError:
                return int(float(row_item))
        else:
            return None

    def nullable_string(self, row_item):
        if row_item.strip():
            return row_item.strip()
        else:
            return None

    def nullable_decimal(self, row_item):
        if row_item.strip():
            return Decimal(row_item.strip()).quantize(Decimal('.001'))
        else:
            return None

    def load_region_data(self, data_date, zfile):
        """ Region represents bank regions (mapping regions to states). This
        loads the data from the daily CSV we receive. """

        filename = "%s_region.txt" % data_date
        data_date = timezone.make_aware(
            datetime.strptime(data_date, '%Y%m%d'),
            timezone.get_current_timezone())
        region_reader = reader(StringIO.StringIO(zfile.read(filename)), delimiter='\t')

        iter_region = iter(region_reader)
        next(iter_region)

        regions = []
        total_regions = 0
        for row in iter_region:
            total_regions += 1
            r = Region()
            r.region_id = int(row[0])
            r.state_id = row[1]
            r.data_timestamp = data_date
            regions.append(r)

            if len(regions) > 1000:
                #Batching the bulk_creates prevents the command from
                #running out of memory.
                Region.objects.bulk_create(regions)
                regions[:] = []

        Region.objects.bulk_create(regions)
        if not total_regions or Region.objects.count() != total_regions:
            raise OaHException("Couldn't load region data from %s" % zfile.filename)

    def load_adjustment_data(self, data_date, zfile):
        """ Read the adjustment CSV file and create. """

        filename = "%s_adjustment.txt" % data_date
        data_date = timezone.make_aware(
            datetime.strptime(data_date, '%Y%m%d'),
            timezone.get_current_timezone())
        adjustment_reader = reader(StringIO.StringIO(zfile.read(filename)), delimiter='\t')

        iteradjustment = iter(adjustment_reader)
        next(iteradjustment)

        adjustments = []
        total_adjustments = 0
        for row in iteradjustment:
            total_adjustments += 1
            a = Adjustment()
            a.product_id = int(row[0])
            a.rule_id = int(row[1])
            a.affect_rate_type = row[2]
            adj_value = self.nullable_decimal(row[3])
            a.adj_value = adj_value if adj_value is not None else 0
            a.min_loan_amt = self.nullable_decimal(row[4])
            a.max_loan_amt = self.nullable_decimal(row[5].strip())
            a.prop_type = self.nullable_string(row[6])
            a.min_fico = self.nullable_int(row[7])
            a.max_fico = self.nullable_int(row[8])
            a.min_ltv = self.nullable_decimal(row[9])
            a.max_ltv = self.nullable_decimal(row[10])
            a.state = row[11]
            a.data_timestamp = data_date
            adjustments.append(a)

            if len(adjustments) > 1000:
                Adjustment.objects.bulk_create(adjustments)
                adjustments[:] = []

        Adjustment.objects.bulk_create(adjustments)
        if not total_adjustments or Adjustment.objects.count() != total_adjustments:
            raise OaHException("Couldn't load adjustment data from %s" % zfile.filename)

    def load_product_data(self, data_date, zfile):
        """ Load the daily product data."""
        filename = "%s_product.txt" % data_date
        data_date = timezone.make_aware(
            datetime.strptime(data_date, '%Y%m%d'),
            timezone.get_current_timezone())

        product_reader = reader(StringIO.StringIO(zfile.read(filename)), delimiter='\t')

        #Skip the first row as it contains column documentation
        iterproducts = iter(product_reader)
        next(iterproducts)

        products = []
        total_products = 0
        for row in iterproducts:
            total_products += 1
            p = Product()
            p.plan_id = int(row[0])
            p.institution = row[1]
            p.loan_purpose = row[2]
            p.pmt_type = row[3]
            p.loan_type = row[4]
            p.loan_term = int(row[5])
            p.int_adj_term = self.nullable_int(row[6])
            p.adj_period = self.nullable_int(row[7])
            p.io = self.string_to_boolean(row[8])
            p.arm_index = self.nullable_string(row[9])
            p.int_adj_cap = self.nullable_int(row[10])

            p.annual_cap = self.nullable_int(row[11])
            p.loan_cap = self.nullable_int(row[12])
            p.arm_margin = self.nullable_decimal(row[13])
            p.ai_value = self.nullable_decimal(row[14])

            p.min_ltv = Decimal(row[15]).quantize(Decimal('.001'))
            p.max_ltv = Decimal(row[16]).quantize(Decimal('.001'))
            p.min_fico = int(row[17])
            p.max_fico = int(row[18])
            p.min_loan_amt = Decimal(row[19])
            p.max_loan_amt = Decimal(row[20])

            p.data_timestamp = data_date
            products.append(p)

            if len(products) > 1000:
                Product.objects.bulk_create(products)
                products[:] = []

        Product.objects.bulk_create(products)
        if not total_products or Product.objects.count() != total_products:
            raise OaHException("Couldn't load product data from %s" % zfile.filename)

    def create_rate(self, row, data_date):
        """ Create a Rate object from a row of the CSV file. """
        r = Rate()
        r.rate_id = int(row[0])
        r.product_id = int(row[1])
        r.lock = int(row[3])
        r.base_rate = Decimal(row[4])
        r.total_points = Decimal(row[5])
        r.data_timestamp = data_date
        r.region_id = int(row[2])
        return r

    def load_rate_data(self, data_date, zfile):
        """ Load the daily rate data from a CSV file. """

        filename = "%s_rate.txt" % data_date
        data_date = timezone.make_aware(
            datetime.strptime(data_date, '%Y%m%d'),
            timezone.get_current_timezone())
        rate_reader = reader(StringIO.StringIO(zfile.read(filename)), delimiter='\t')

        iterrates = iter(rate_reader)
        next(iterrates)

        rates = []
        total_rates = 0
        for row in iterrates:
            total_rates += 1
            r = self.create_rate(row, data_date)
            rates.append(r)

            if len(rates) > 1000:
                Rate.objects.bulk_create(rates)
                rates[:] = []
        Rate.objects.bulk_create(rates)
        if not total_rates or Rate.objects.count() != total_rates:
            raise OaHException("Couldn't load rate data from %s" % zfile.filename)

    def get_precalculated_results(self, zfile):
        """ Parse an xml file for pre-calculated results for the scenarios."""
        data = {}
        filename = 'CoverSheet.xml'
        tree = ET.parse(StringIO.StringIO(zfile.read(filename)))
        for scenario in tree.getiterator(tag='Scenario'):
            temp = {}
            for elem in scenario:
                temp[elem.tag] = elem.text
            data[temp['ScenarioNo']] = [temp['AdjustedRates'], temp['AdjustedPoints']]
        return data

    def compare_scenarios_output(self, precalculated_results):
        """ Run scenarios thru API, compare results to <precalculated_results>."""
        passed = True
        failed = []
        for scenario_no in self.test_scenarios:
            # since these scenarios use loan_type=AGENCY
            if scenario_no in ['16', '42' ]:
                continue
            rcparams = RateCheckerParameters()
            rcparams.set_from_query_params(self.test_scenarios[scenario_no])
            api_result = get_rates(rcparams, data_load_testing=True)
            expected_rate = "%s" % precalculated_results[scenario_no][0]
            expected_points = precalculated_results[scenario_no][1]
            if len(api_result['data']) > 1 or\
                    expected_rate not in api_result['data'] or\
                    expected_points != api_result['data'][expected_rate]:

                if expected_rate is not None and api_result['data']:
                    passed = False
                    failed.append(scenario_no)

        if not passed:
            failed.sort(key=int)
            self.messages.append("The following scenarios don't match: %s " % failed)
            #raise OaHException("The following scenarios don't match: %s" % failed)

    def archive_data_to_temp_tables(self, cursor):
        """ Save data to temporary tables and delete it from normal tables."""
        # decided not to use TEMPORARY MySQL tables, because loosing data was too easy
        self.delete_temp_tables(cursor)

        cursor.execute('CREATE TABLE temporary_product AS SELECT * FROM ratechecker_product')
        cursor.execute('CREATE TABLE temporary_region AS SELECT * FROM ratechecker_region')
        cursor.execute('CREATE TABLE temporary_rate AS SELECT * FROM ratechecker_rate')
        cursor.execute('CREATE TABLE temporary_adjustment AS SELECT * FROM ratechecker_adjustment')

    def delete_temp_tables(self, cursor):
        """ Delete temporary tables."""
        cursor.execute('DROP TABLE IF EXISTS temporary_product')
        cursor.execute('DROP TABLE IF EXISTS temporary_region')
        cursor.execute('DROP TABLE IF EXISTS temporary_rate')
        cursor.execute('DROP TABLE IF EXISTS temporary_adjustment')

    def delete_data_from_base_tables(self):
        """ Delete current data."""
        Product.objects.all().delete()
        Rate.objects.all().delete()
        Region.objects.all().delete()
        Adjustment.objects.all().delete()

    def reload_old_data(self, cursor):
        """ Move data from temporary tables back into the base tables."""
        cursor.execute('INSERT INTO ratechecker_product SELECT * FROM temporary_product')
        cursor.execute('INSERT INTO ratechecker_adjustment SELECT * FROM temporary_adjustment')
        cursor.execute('INSERT INTO ratechecker_rate SELECT * FROM temporary_rate')
        cursor.execute('INSERT INTO ratechecker_region SELECT * FROM temporary_region')

    def output_messages(self):
        """ Need this for fabric-jenkins to work."""
        for line in self.messages:
            print line
