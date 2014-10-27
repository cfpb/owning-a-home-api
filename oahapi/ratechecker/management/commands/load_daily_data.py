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

import warnings
import _mysql_exceptions

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from django.db.utils import OperationalError, IntegrityError

from ratechecker.models import Product, Adjustment, Region, Rate

ARCHIVE_PATTERN = '^\d{8}\.zip$'


class OaHException(Exception):
    pass


class Command(BaseCommand):
    args = "<directory_path>"
    help = """ Loads daily interest rate data from a zip archive with CSV files. """
    messages = []
    status = 1     # 1 = FAILURE, 0 = SUCCESS

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

        if bstr.lower() == 'true':
            return True
        elif bstr.lower() == 'false':
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
