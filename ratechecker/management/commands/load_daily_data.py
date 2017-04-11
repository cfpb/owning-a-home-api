from __future__ import print_function

import StringIO
import argparse
import os
import re
import traceback
import warnings
import zipfile

from csv import reader
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone

from ratechecker.models import Product, Adjustment, Region, Rate, Fee
from ratechecker.validation import ScenarioValidator


class OaHException(Exception):
    pass


def latest_archive(folder):
    """Returns latest archive filename matching YYYYMMDD.zip."""
    try:
        filenames = os.listdir(folder)
    except OSError:
        raise argparse.ArgumentTypeError('invalid path: {}'.format(folder))

    archives = [
        os.path.join(folder, name) for name in filenames
        if re.match(r'^\d{8}\.zip$', name)
    ]

    if not archives:
        raise argparse.ArgumentTypeError(
            'no matching archives in {}'.format(folder)
        )

    if archives:
        return sorted(archives, reverse=True)[0]


class Command(BaseCommand):
    help = 'Loads daily interest rate data from a zip archive with CSV files.'

    def add_arguments(self, parser):
        parser.add_argument(
            'data_dir', type=latest_archive,
            help='Path containing interest rate data files'
        )
        parser.add_argument(
            '-s', '--validation-scenario-file', required=True,
            type=argparse.FileType('r'),
            help='JSON-line file containing validation scenario parameters'
        )
        parser.add_argument(
            '--validate-only', action='store_true',
            help='Skip load and revalidate existing table'
        )

    def handle(self, **options):
        warnings.filterwarnings('ignore', 'Unknown table.*')

        archive = options['data_dir']
        validate_only = options['validate_only']
        validation_file = options['validation_scenario_file']
        verbosity = options['verbosity']

        if not validate_only:
            if verbosity:
                print('Copying data to temp tables')

            self.archive_data_to_temp_tables()

        try:
            if not validate_only:
                if verbosity:
                    print('Loading data from', archive)

                self.load_archive_data(archive)

            if validation_file:
                if verbosity:
                    print('Validating loaded data with', validation_file.name)

                validator = ScenarioValidator(verbose=verbosity)
                validator.validate_file(validation_file, archive)
        except Exception:
            traceback.print_exc()

            if not validate_only:
                if verbosity:
                    print('Restoring old data')

                self.delete_data_from_base_tables()
                self.reload_old_data()

            raise CommandError('Load failed')
        finally:
            if not validate_only:
                if verbosity:
                    print('Cleaning up temp tables')

                self.delete_temp_tables()

        if verbosity:
            print('Load successful')

    def load_archive_data(self, archive):
        """ Load data from zipfile."""
        with zipfile.ZipFile(archive) as zf:
            date = zf.filename[:-4]
            date = date.split('/')[-1]
            self.load_product_data(date, zf)
            self.load_adjustment_data(date, zf)
            self.load_rate_data(date, zf)
            self.load_region_data(date, zf)
            self.load_fee_data(date, zf)

    @staticmethod
    def string_to_boolean(bstr):
        """ If bstr is 'True' return True. If bstr is 'False' return False.
        Otherwise return None. This is case-insensitive.  """

        if bstr.lower() == 'true' or bstr == '1':
            return True
        elif bstr.lower() == 'false' or bstr == '0':
            return False

    @staticmethod
    def nullable_int(row_item):
        if row_item.strip():
            try:
                return int(row_item)
            except ValueError:
                return int(float(row_item))
        else:
            return None

    @staticmethod
    def nullable_string(row_item):
        if row_item.strip():
            return row_item.strip()
        else:
            return None

    @staticmethod
    def nullable_decimal(row_item):
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

    def create_fee(self, row, data_date):
        """ Create a Fee object from a row of the CSV file. """
        f = Fee()
        f.plan_id = int(row[0])
        f.product_id = int(row[1])
        f.state_id = row[2]
        f.lender = row[3]
        f.single_family = bool(int(row[4]))
        f.condo = bool(int(row[5]))
        f.coop = bool(int(row[6]))
        f.origination_dollar = Decimal(row[7])
        f.origination_percent = Decimal(row[8])
        f.third_party = Decimal(row[9])
        f.data_timestamp = data_date
        return f

    def load_fee_data(self, data_date, zfile):
        """ Load the fee data from a CSV file. """

        filename = "%s_fee.txt" % data_date
        data_date = timezone.make_aware(
            datetime.strptime(data_date, '%Y%m%d'),
            timezone.get_current_timezone())
        fee_reader = reader(StringIO.StringIO(zfile.read(filename)), delimiter='\t')

        iterfees = iter(fee_reader)
        next(iterfees)

        fees = []
        total_fees = 0
        for row in iterfees:
            total_fees += 1
            f = self.create_fee(row, data_date)
            fees.append(f)

            if len(fees) > 1000:
                Fee.objects.bulk_create(fees)
                fees[:] = []

        Fee.objects.bulk_create(fees)
        if not total_fees or Fee.objects.count() != total_fees:
            raise OaHException("Couldn't load fee data from %s" % zfile.filename)

    def archive_data_to_temp_tables(self):
        """ Save data to temporary tables and delete it from normal tables."""
        self.delete_temp_tables()

        cursor = connection.cursor()
        cursor.execute('CREATE TABLE temporary_product AS SELECT * FROM ratechecker_product')
        cursor.execute('CREATE TABLE temporary_region AS SELECT * FROM ratechecker_region')
        cursor.execute('CREATE TABLE temporary_rate AS SELECT * FROM ratechecker_rate')
        cursor.execute('CREATE TABLE temporary_adjustment AS SELECT * FROM ratechecker_adjustment')
        cursor.execute('CREATE TABLE temporary_fee AS SELECT * FROM ratechecker_fee')

        self.delete_data_from_base_tables()

    def delete_temp_tables(self):
        """ Delete temporary tables."""
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS temporary_product')
        cursor.execute('DROP TABLE IF EXISTS temporary_region')
        cursor.execute('DROP TABLE IF EXISTS temporary_rate')
        cursor.execute('DROP TABLE IF EXISTS temporary_adjustment')
        cursor.execute('DROP TABLE IF EXISTS temporary_fee')

    def delete_data_from_base_tables(self):
        """ Delete current data."""
        Product.objects.all().delete()
        Rate.objects.all().delete()
        Region.objects.all().delete()
        Adjustment.objects.all().delete()
        Fee.objects.all().delete()

    def reload_old_data(self):
        """ Move data from temporary tables back into the base tables."""
        cursor = connection.cursor()
        cursor.execute('INSERT INTO ratechecker_product SELECT * FROM temporary_product')
        cursor.execute('INSERT INTO ratechecker_adjustment SELECT * FROM temporary_adjustment')
        cursor.execute('INSERT INTO ratechecker_rate SELECT * FROM temporary_rate')
        cursor.execute('INSERT INTO ratechecker_region SELECT * FROM temporary_region')
        cursor.execute('INSERT INTO ratechecker_fee SELECT * FROM temporary_fee')
