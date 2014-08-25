from csv import reader
import os
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from ratechecker.models import Product, Adjustment, Region, Rate


class Command(BaseCommand):
    args = "<directory_path>"
    help = """ Loads daily interest rate data from CSV files.
        All files are in one directory. """

    def get_date_from_filename(self, file_name):
        """ The data corresponding to the data is part of the filename. We
        extract that here. """

        for dstr in file_name.split('_'):
            try:
                file_date = datetime.strptime(dstr, '%Y%m%d')
                return file_date
            except ValueError:
                pass
        raise ValueError('No date in filename')

    def get_data_file_paths(self, directory_name):
        """ Get the files paths and some metadata about the data load.  We try
        not to assume too much about the data file names at this point.  """

        data = {}
        data_files = {}

        for root, _, files in os.walk(directory_name):
            for name in files:
                data_path = os.path.join(root, name)
                if 'product' in name:
                    data_files['product'] = data_path
                elif 'region' in name:
                    data_files['region'] = data_path
                elif 'rate' in name:
                    data_files['rate'] = data_path
                elif 'adjustment' in name:
                    data_files['adjustment'] = data_path
        data_date = self.get_date_from_filename(data_files['product'])

        data['date'] = data_date
        data['file_names'] = data_files
        return data

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

        with open(region_filename) as region_csv:
            region_reader = reader(region_csv, delimiter='\t')

            iter_region = iter(region_reader)
            next(iter_region)

            regions = []
            for row in iter_region:
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

    def load_adjustment_data(self, data_date, adjustment_filename):
        """ Read the adjustment CSV file and create. """

        with open(adjustment_filename) as adjustment_csv:
            adjustment_reader = reader(adjustment_csv, delimiter='\t')

            iteradjustment = iter(adjustment_reader)
            next(iteradjustment)

            adjustments = []
            for row in iteradjustment:
                a = Adjustment()

                a.product_id = int(row[0])
                a.rule_id = int(row[1])
                a.affect_rate_type = row[2]
                a.adj_value = self.nullable_decimal(row[3])
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

    def load_product_data(self, data_date, product_filename):
        """ Load the daily product data."""

        with open(product_filename) as product_csv:
            product_reader = reader(product_csv, delimiter='\t')

            #Skip the first row as it contains column documentation
            iterproducts = iter(product_reader)
            next(iterproducts)

            products = []
            for row in iterproducts:

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

        with open(rate_filename) as rate_csv:
            rate_reader = reader(rate_csv, delimiter='\t')

            iterrates = iter(rate_reader)
            next(iterrates)

            rates = []
            for row in iterrates:
                r = self.create_rate(row, data_date)
                rates.append(r)

                if len(rates) > 1000:
                    Rate.objects.bulk_create(rates)
                    rates[:] = []
            Rate.objects.bulk_create(rates)

    def handle(self, *args, **options):
        """ Given a directory containing the days files, this command will load
        all the data for that day. """

        data_information = self.get_data_file_paths(args[0])

        self.load_product_data(
            data_information['date'],
            data_information['file_names']['product'])

        self.load_adjustment_data(
            data_information['date'],
            data_information['file_names']['adjustment'])

        self.load_region_data(
            data_information['date'],
            data_information['file_names']['region'])

        self.load_rate_data(
            data_information['date'],
            data_information['file_names']['rate'])
