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
from ratechecker.views import RateCheckerParameters, rate_query

ARCHIVE_PATTERN = '^\d{8}\.zip$'


class OaHException(Exception):
    pass


class Command(BaseCommand):
    args = "<directory_path>"
    help = """ Loads daily interest rate data from a zip archive with CSV files. """
    messages = []
    status = 1     # 1 = FAILURE, 0 = SUCCESS

    test_scenarios = {
        '1': {'arm_type': '', 'loan_type': 'VA', 'io': '', 'loan_amount': 150000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 640, 'state': 'AK', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Bank of America', 'ltv': 100},
        '2': {'arm_type': '', 'loan_type': 'VA', 'io': '', 'loan_amount': 200000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 690, 'state': 'AL', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'BBVA Compass', 'ltv': 95},
        '3': {'arm_type': 3, 'loan_type': 'CONF', 'io': '', 'loan_amount': 75000,
                'lock': 45, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 710, 'state': 'AR', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'PNC Mortgage', 'ltv': 90},
        '4': {'arm_type': 3, 'loan_type': 'CONF', 'io': 1.0, 'loan_amount': 400000,
                'lock': 60, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 745, 'state': 'AZ', 'purpose': 'PURCH', 'data': 'N',
                'institution': 'US Bank', 'ltv': 90},
        '5': {'arm_type': '', 'loan_type': 'JUMBO', 'io': '', 'loan_amount': 900000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 760, 'state': 'CA', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Union Bank', 'ltv': 80},
        '6': {'arm_type': '', 'loan_type': 'CONF', 'io': '', 'loan_amount': 350000,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 740, 'state': 'CA', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Patelco Credit Union', 'ltv': 85},
        '7': {'arm_type': '', 'loan_type': 'JUMBO', 'io': '', 'loan_amount': 1500000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 780, 'state': 'CO', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'FirstBank Colorado', 'ltv': 75},
        '8': {'arm_type': 7, 'loan_type': 'AGENCY', 'io': 1.0, 'loan_amount': 525000,
                'lock': 30, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 715, 'state': 'CT', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'RBS Citizens', 'ltv': 85},
        '9': {'arm_type': '', 'loan_type': 'FHA-HB', 'io': '', 'loan_amount': 600000,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 660, 'state': 'DC', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Quicken Loans', 'ltv': 95},
        '10': {'arm_type': '', 'loan_type': 'CONF', 'io': '', 'loan_amount': 175000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 690, 'state': 'DE', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'Capital One', 'ltv': 75},
        '11': {'arm_type': '', 'loan_type': 'CONF', 'io': '', 'loan_amount': 275000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 780, 'state': 'FL', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Kinecta FCU', 'ltv': 90},
        '12': {'arm_type': 3, 'loan_type': 'JUMBO', 'io': '', 'loan_amount': 700000,
                'lock': 45, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 800, 'state': 'GA', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'First Tech FCU', 'ltv': 70},
        '13': {'arm_type': '', 'loan_type': 'AGENCY', 'io': '', 'loan_amount': 700000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 720, 'state': 'HI', 'purpose': 'REFI', 'data': 'N',
                'institution': 'PNC Mortgage', 'ltv': 85},
        '14': {'arm_type': 5, 'loan_type': 'CONF', 'io': '', 'loan_amount': 200000,
                'lock': 30, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 680, 'state': 'IA', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Fifth Third Bank', 'ltv': 90},
        '15': {'arm_type': '', 'loan_type': 'FHA', 'io': '', 'loan_amount': 100000,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 650, 'state': 'ID', 'purpose': 'REFI', 'data': 'N',
                'institution': 'Zions Bank', 'ltv': 95},
        '16': {'arm_type': '', 'loan_type': 'AGENCY', 'io': '', 'loan_amount': 600000,
                'lock': 60, 'proptype': 'CONDO', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 690, 'state': 'IL', 'purpose': 'REFI', 'data': 'N',
                'institution': 'Astoria Federal Savings', 'ltv': 80},
        '17': {'arm_type': '', 'loan_type': 'FHA', 'io': '', 'loan_amount': 150000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 710, 'state': 'IN', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'CitiMortgage', 'ltv': 95},
        '18': {'arm_type': '', 'loan_type': 'CONF', 'io': '', 'loan_amount': 250000,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 760, 'state': 'KS', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'Boeing Employees Credit Union', 'ltv': 90},
        '19': {'arm_type': '', 'loan_type': 'VA', 'io': '', 'loan_amount': 150000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 715, 'state': 'KY', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'Fifth Third Bank', 'ltv': 75},
        '20': {'arm_type': 5, 'loan_type': 'CONF', 'io': '', 'loan_amount': 100000,
                'lock': 30, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 695, 'state': 'LA', 'purpose': 'PURCH', 'data': 'N',
                'institution': 'Regions Bank', 'ltv': 93},
        '21': {'arm_type': 10, 'loan_type': 'CONF', 'io': '', 'loan_amount': 400000,
                'lock': 45, 'proptype': 'CONDO', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 765, 'state': 'MA', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'Webster Bank', 'ltv': 75},
        '22': {'arm_type': 7, 'loan_type': 'AGENCY', 'io': '', 'loan_amount': 550000,
                'lock': 60, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 780, 'state': 'MD', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'TD Bank', 'ltv': 80},
        '23': {'arm_type': '', 'loan_type': 'CONF', 'io': '', 'loan_amount': 120000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 750, 'state': 'ME', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'TD Bank', 'ltv': 70},
        '24': {'arm_type': '', 'loan_type': 'FHA', 'io': '', 'loan_amount': 180000,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 680, 'state': 'MI', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'HSBC', 'ltv': 80},
        '25': {'arm_type': 10, 'loan_type': 'CONF', 'io': '', 'loan_amount': 400000,
                'lock': 60, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 790, 'state': 'MN', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'Charles Schwab', 'ltv': 85},
        '26': {'arm_type': '', 'loan_type': 'FHA', 'io': '', 'loan_amount': 150000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 710, 'state': 'MO', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'BMO Harris', 'ltv': 90},
        '27': {'arm_type': '', 'loan_type': 'CONF', 'io': '', 'loan_amount': 80000,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 705, 'state': 'MS', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'PNC Mortgage', 'ltv': 80},
        '28': {'arm_type': 5, 'loan_type': 'CONF', 'io': '', 'loan_amount': 400000,
                'lock': 60, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 740, 'state': 'MT', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'State Farm Bank', 'ltv': 85},
        '29': {'arm_type': '', 'loan_type': 'FHA-HB', 'io': '', 'loan_amount': 350000,
                'lock': 30, 'proptype': 'CONDO', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 690, 'state': 'NC', 'purpose': 'PURCH', 'data': 'N',
                'institution': 'Chase', 'ltv': 95},
        '30': {'arm_type': '', 'loan_type': 'CONF', 'io': '', 'loan_amount': 100500,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 705, 'state': 'ND', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'State Farm Bank', 'ltv': 80},
        '31': {'arm_type': '', 'loan_type': 'FHA', 'io': '', 'loan_amount': 250000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 710, 'state': 'NE', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'Bank of America', 'ltv': 96.5},
        '32': {'arm_type': '', 'loan_type': 'FHA-HB', 'io': '', 'loan_amount': 400000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 740, 'state': 'NH', 'purpose': 'PURCH', 'data': 'N',
                'institution': 'Santander Bank', 'ltv': 95},
        '33': {'arm_type': '', 'loan_type': 'VA-HB', 'io': '', 'loan_amount': 450000,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 680, 'state': 'NJ', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'CitiMortgage', 'ltv': 100},
        '34': {'arm_type': 3, 'loan_type': 'CONF', 'io': '', 'loan_amount': 250000,
                'lock': 60, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 720, 'state': 'NM', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'State Farm Bank', 'ltv': 85},
        '35': {'arm_type': 7, 'loan_type': 'CONF', 'io': '', 'loan_amount': 417000,
                'lock': 30, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 745, 'state': 'NV', 'purpose': 'REFI', 'data': 'N',
                'institution': 'Zions Bank', 'ltv': 83},
        '36': {'arm_type': '', 'loan_type': 'CONF', 'io': '', 'loan_amount': 400000,
                'lock': 45, 'proptype': 'COOP', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 695, 'state': 'NY', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Wells Fargo', 'ltv': 80},
        '37': {'arm_type': '', 'loan_type': 'VA', 'io': '', 'loan_amount': 200000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 710, 'state': 'OH', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Huntington National Bank', 'ltv': 98.0},
        '38': {'arm_type': '', 'loan_type': 'FHA', 'io': '', 'loan_amount': 50000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 650, 'state': 'OK', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Chase', 'ltv': 90},
        '39': {'arm_type': 5, 'loan_type': 'CONF', 'io': '', 'loan_amount': 150000,
                'lock': 45, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 730, 'state': 'OR', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'OnPoint Community CU', 'ltv': 95},
        '40': {'arm_type': '', 'loan_type': 'FHA', 'io': '', 'loan_amount': 250000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 725, 'state': 'PA', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'First Niagra', 'ltv': 85},
        '41': {'arm_type': '', 'loan_type': 'FHA-HB', 'io': '', 'loan_amount': 300000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 690, 'state': 'RI', 'purpose': 'REFI', 'data': 'N',
                'institution': 'Charles Schwab', 'ltv': 95},
        '42': {'arm_type': '', 'loan_type': 'AGENCY', 'io': '', 'loan_amount': 600000,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 780, 'state': 'SC', 'purpose': 'PURCH', 'data': 'N',
                'institution': 'Capital One', 'ltv': 80},
        '43': {'arm_type': '', 'loan_type': 'CONF', 'io': '', 'loan_amount': 60000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 750, 'state': 'SD', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'State Farm Bank', 'ltv': 90},
        '44': {'arm_type': '', 'loan_type': 'FHA', 'io': '', 'loan_amount': 60000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 630, 'state': 'TN', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'RBS Citizens', 'ltv': 95},
        '45': {'arm_type': '', 'loan_type': 'FHA', 'io': '', 'loan_amount': 250000,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 680, 'state': 'TX', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Regions Bank', 'ltv': 95},
        '46': {'arm_type': '', 'loan_type': 'JUMBO', 'io': '', 'loan_amount': 425000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 780, 'state': 'UT', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Kinecta FCU', 'ltv': 75},
        '47': {'arm_type': '', 'loan_type': 'VA-HB', 'io': '', 'loan_amount': 575000,
                'lock': 30, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 710, 'state': 'VA', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'HSBC', 'ltv': 95},
        '48': {'arm_type': '', 'loan_type': 'JUMBO', 'io': '', 'loan_amount': 800000,
                'lock': 45, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 740, 'state': 'VT', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'Quicken Loans', 'ltv': 80},
        '49': {'arm_type': '', 'loan_type': 'VA', 'io': '', 'loan_amount': 250000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 15,
                'fico': 705, 'state': 'WA', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'First Federal', 'ltv': 90},
        '50': {'arm_type': 10, 'loan_type': 'CONF', 'io': '', 'loan_amount': 350000,
                'lock': 30, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 750, 'state': 'WI', 'purpose': 'PURCH', 'data': 'Y',
                'institution': 'BMO Harris', 'ltv': 95},
        '51': {'arm_type': 10, 'loan_type': 'AGENCY', 'io': 1.0, 'loan_amount': 550000,
                'lock': 45, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 790, 'state': 'WV', 'purpose': 'REFI', 'data': 'Y',
                'institution': 'US Bank', 'ltv': 80},
        '52': {'arm_type': 5, 'loan_type': 'JUMBO', 'io': 1.0, 'loan_amount': 500000,
                'lock': 60, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 750, 'state': 'WY', 'purpose': 'PURCH', 'data': 'N',
                'institution': 'PNC Mortgage', 'ltv': 85},
        '53': {'arm_type': '', 'loan_type': 'CONF', 'io': '', 'loan_amount': 200000,
                'lock': 60, 'proptype': '', 'rate_structure': 'Fixed', 'loan_term': 30,
                'fico': 740, 'state': 'CA', 'purpose': 'PURCH', 'data': '',
                'institution': 'Wells Fargo', 'ltv': 70},
        '54': {'arm_type': '5', 'loan_type': 'CONF', 'io': '', 'loan_amount': 200000,
                'lock': 60, 'proptype': '', 'rate_structure': 'ARM', 'loan_term': 30,
                'fico': 740, 'state': 'CA', 'purpose': 'PURCH', 'data': '',
                'institution': 'Bank of America', 'ltv': 80}
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
            return Decimal(row_item.strip())
        else:
            return None

    def nullable_float(self, row_item):
        if row_item.strip():
            return float(row_item.strip())
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
            a.min_ltv = self.nullable_float(row[9])
            a.max_ltv = self.nullable_float(row[10])
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

            p.min_ltv = float(row[15])
            p.max_ltv = float(row[16])
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

    def _comb_test_scenarios(self):
        for ndx, sc in self.test_scenarios.iteritems():
            sc['price'] = sc['loan_amount'] * 100 / sc['ltv']
            sc['arm_type'] = '%s-1' % sc['arm_type']
            sc['maxfico'] = sc['minfico'] = sc['fico']

    def compare_scenarios_output(self, precalculated_results):
        """ Run scenarios thru API, compare results to <precalculated_results>."""
        passed = True
        failed = []
        self._comb_test_scenarios()
        for scenario_no in self.test_scenarios:
            rcparams = RateCheckerParameters()
            rcparams.set_from_query_params(self.test_scenarios[scenario_no])
            api_result = rate_query(rcparams, data_load_testing=False)
            if precalculated_results[scenario_no][1] in api_result:
                passed = False
                failed.append(scenario_no)

        if not passed:
            raise OaHException("The following scenarios don't match: %s" % failed.sort(key=int))

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
