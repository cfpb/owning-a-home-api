from csv import reader
import os
import re
from datetime import datetime
from decimal import Decimal
from operator import itemgetter
import warnings
import _mysql_exceptions

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage

from ratechecker.models import Product, Adjustment, Region, Rate

FILENAME_PATTERN = '^(\d{8})_(product|adjustment|rate|region)\.csv$'
FILES_NOT_FOUND = 'Not all necessary files were found'
SUCCESS_SUBJECT = 'Successfully loaded new data'
ERROR_SUBJECT = 'Failed to load new data'
ERROR_MESSAGE = 'There was an error while loading new data'
NOTIFICATION_BODY = '%s\n\nThe folowing files were processed:\n%s'


class OaHException(Exception):
    pass


class Command(BaseCommand):
    args = "<directory_path>"
    help = """ Loads daily interest rate data from CSV files.
        All files are in one directory. """
    status = 1
    message = ''

    def handle(self, *args, **options):
        # Get rid of runtime errors caused by MySQL warnings for IF EXISTS query
        warnings.filterwarnings('ignore', category=_mysql_exceptions.Warning)

        self.stdout.write('\nOnly files named YYYYMMDD_(product|adjustment|region|rate).csv will be processed.\n\n')
        self.stdout.write('Files will be deleted after the data is loaded successfully.\n\n')

        cursor = connection.cursor()
        files = {}
        try:
            files = self.read_filenames(args[0])
            self.archive_data_to_temp_tables(cursor)
            self.load_new_data(files, cursor)
            self.delete_data_files(files)
        except OaHException as e:
            self.status = 0
            self.message = str(e)
        finally:
            self.delete_temp_tables(cursor)
            self.stdout.write(SUCCESS_SUBJECT if self.status else ERROR_SUBJECT)
            self.email_status(files)

    def delete_temp_tables(self, cursor):
        """ Delete temporary tables."""
        self.stdout.write(' Deleting temporary tables...')
        cursor.execute('DROP TABLE IF EXISTS temporary_product')
        cursor.execute('DROP TABLE IF EXISTS temporary_region')
        cursor.execute('DROP TABLE IF EXISTS temporary_rate')
        cursor.execute('DROP TABLE IF EXISTS temporary_adjustment')

    def load_new_data(self, files, cursor):
        """ Load new data, check itegrity, (optionally move old data back), delete olddata tables, show status."""
        self.stdout.write(' Loading new data...')
        if not self.load_product_data(files['product']['date'], files['product']['file']) or\
           not self.load_adjustment_data(files['adjustment']['date'], files['adjustment']['file']) or\
           not self.load_rate_data(files['rate']['date'], files['rate']['file']) or\
           not self.load_region_data(files['region']['date'], files['region']['file']):
            self.reload_old_data(cursor)
            raise OaHException(ERROR_MESSAGE)

    def email_status(self, files):
        """ Send status of data loading to addresses from OAH_NOTIFY_EMAILS."""
        bug_people = settings.OAH_NOTIFY_EMAILS
        if not bug_people:
            self.stderr.write(' Please set OAH_NOTIFY_EMAILS env var, with a comma separated list of emails of people to bug.')
            return
        subject = SUCCESS_SUBJECT if self.status else ERROR_SUBJECT
        body = NOTIFICATION_BODY % (self.message, [files[file]['file'] for file in files])
        email = EmailMessage(subject, body, to=bug_people)
        email.send()

    def delete_data_files(self, files):
        """ Remove data files."""
        self.stdout.write(' Removing data files...')
        for item in files:
            os.remove(files[item]['file'])

    def reload_old_data(self, cursor):
        """ Move data from temporary tables back into the base tables."""
        self.stdout.write(' Reloading old data...')
        self.delete_data_from_base_tables()
        cursor.execute('INSERT INTO ratechecker_product SELECT * FROM temporary_product')
        cursor.execute('INSERT INTO ratechecker_adjustment SELECT * FROM temporary_adjustment')
        cursor.execute('INSERT INTO ratechecker_rate SELECT * FROM temporary_rate')
        cursor.execute('INSERT INTO ratechecker_region SELECT * FROM temporary_region')

    def archive_data_to_temp_tables(self, cursor):
        """ Save data to temporary tables and delete it from normal tables."""
        self.stdout.write(' Archiving data to temporary tables...')
        # decided not to use TEMPORARY tables, because loosing data is too easy

        self.delete_temp_tables(cursor)

        cursor.execute('CREATE TABLE temporary_product AS (SELECT * FROM ratechecker_product)')
        cursor.execute('CREATE TABLE temporary_region AS (SELECT * FROM ratechecker_region)')
        cursor.execute('CREATE TABLE temporary_rate AS (SELECT * FROM ratechecker_rate)')
        cursor.execute('CREATE TABLE temporary_adjustment AS (SELECT * FROM ratechecker_adjustment)')

        self.delete_data_from_base_tables()

    def delete_data_from_base_tables(self):
        """ Delete current data."""
        self.stdout.write(' Deleting data...')
        Product.objects.all().delete()
        Rate.objects.all().delete()
        Region.objects.all().delete()
        Adjustment.objects.all().delete()

    def read_filenames(self, directory_name):
        """ Read the provided directory. Check that we all 4 necessary files and their dates are the same."""
        self.stdout.write(' Reading files from %s...' % directory_name)
        data_files = []
        for name in os.listdir(directory_name):
            root = directory_name
            data_files.append(self._check_file(name, root))
            data_files = filter(None, data_files)

        return self._check_files(data_files)

    def _check_files(self, data_files):
        """ Check that we have all 4 files."""
        data = {}
        for file_item in data_files:
            tmp = data.get(file_item['date'], [])
            tmp.append(file_item)
            data[file_item['date']] = tmp

        sorted_keys = sorted(data.keys(), reverse=True)
        file_paths = {}
        for key in sorted_keys:
            if len(data[key]) == 4:
                file_paths = dict((item['data'], item) for item in data[key])

        if not file_paths:
            raise OaHException(FILES_NOT_FOUND)

        return file_paths

    def _check_file(self, filename, root):
        """ Check that file is of the required form, not empty and is readable."""
        match = re.match(FILENAME_PATTERN, filename)
        filepath = os.path.join(root, filename)
        if not match or os.path.getsize(filepath) == 0 or not os.access(filepath, os.R_OK):
            self.stderr.write(' %s is not readable or of a not accepted form.' % filename)
            return None
        else:
            date_value = datetime.strptime(match.groups()[0], '%Y%m%d')
            return {
                'date': timezone.make_aware(date_value, timezone.get_current_timezone()),
                'data': match.groups()[1],
                'file': filepath
            }

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

    def load_region_data(self, data_date, region_filename):
        """ Region represents bank regions (mapping regions to states). This
        loads the data from the daily CSV we receive. """
        self.stdout.write(' > Loading Region data from %s...' % region_filename)

        with open(region_filename) as region_csv:
            region_reader = reader(region_csv, delimiter='\t')

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
            return Region.objects.count() == total_regions

    def load_adjustment_data(self, data_date, adjustment_filename):
        """ Read the adjustment CSV file and create. """
        self.stdout.write(' > Loading Adjustment data from %s...' % adjustment_filename)

        with open(adjustment_filename) as adjustment_csv:
            adjustment_reader = reader(adjustment_csv, delimiter='\t')

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
            return Adjustment.objects.count() == total_adjustments

    def load_product_data(self, data_date, product_filename):
        """ Load the daily product data."""
        self.stdout.write(' > Loading Product data from %s...' % product_filename)

        with open(product_filename) as product_csv:
            product_reader = reader(product_csv, delimiter='\t')

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
            return Product.objects.count() == total_products

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

    def load_rate_data(self, data_date, rate_filename):
        """ Load the daily rate data from a CSV file. """
        self.stdout.write(' > Loading Rate data from %s...' % rate_filename)

        with open(rate_filename) as rate_csv:
            rate_reader = reader(rate_csv, delimiter='\t')

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
            return Rate.objects.count() == total_rates
