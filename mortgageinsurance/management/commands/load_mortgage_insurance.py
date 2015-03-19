from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from decimal import Decimal

import csv

from mortgageinsurance.models import Monthly, Upfront

class Command(BaseCommand):
    args = '<file_path> <file_path>'
    help = 'Load mortgage insurance data from two CSV files (monthly and upfront respectively).'
    option_list = BaseCommand.option_list + (
        make_option('--confirm', action='store', dest='confirmed', help='Confirm that you have read the comments'),
    )

    def handle(self, *args, **options):
        self.stdout.write('\n------------------------------------------\n')
        self.stdout.write('\nThis script will first load the monthly mortgage insurance table (file name 1st argument)')
        self.stdout.write('\n *** Monthly Mortgage Insurance ***')
        self.stdout.write('\n1. First row is assumed to have column names, and is skipped while loading data')
        self.stdout.write('\n2. Assumed field order: Mortgage Insurer, Min Loan To Value Ratio, Max Loan To Value Ratio, ' \
                          'Min FICO Score, Max FICO Score, Loan Term, Rate Type, Min Loan Amount, Max Loan Amount, Premium')
        self.stdout.write('\nThis script will then load the upfront mortgage insurance table (file name 2nd argument)')
        self.stdout.write('\n *** Upfront Mortgage Insurance ***')
        self.stdout.write('\n1. First row is assumed to have column names, and is skipped while loading data')
        self.stdout.write('\n2. Assumed field order: Loan Type, VA Status, VA First Use?, Min Loan To Value Ratio, ' \
                          'Max Loan To Value Ratio, Premium')
        self.stdout.write('\n\nAll current data in mortgageinsurance_monthly and mortgageinsurance_upfront tables will be deleted')
        self.stderr.write('\n If you read the above comments and agree, call the command with "--confirm=y" option\n')
        self.stdout.write('\n------------------------------------------\n')

        if options['confirmed'] is None or options['confirmed'].lower() != 'y':
            return

        if len(args) > 1:
            try:
                self.load_monthly(args[0])
                self.load_upfront(args[1])
            except IOError as e:
                raise CommandError(e)
        else:
            raise CommandError('Paths to a CSV monthly mortgage insurance and upfront mortgage insurance files are required.')

    def load_monthly(self, filename):
        with open(filename, 'rU') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')

            # Delete all items in tables
            Monthly.objects.all().delete()

            # Remove the first line which is the header line
            csvreader.next()

            for row in csvreader:

                insurer, min_ltv, max_ltv, min_fico, max_fico, loan_term, pmt_type, min_loan_amt, max_loan_amt, premium = row

                m = Monthly()
                
                m.insurer = insurer.strip().upper()
                m.min_ltv = Decimal(min_ltv)
                m.max_ltv = Decimal(max_ltv)
                m.min_fico = int(min_fico)
                m.max_fico = int(max_fico)
                m.loan_term = int(loan_term)
                m.pmt_type = pmt_type.strip().upper()
                m.min_loan_amt = Decimal(min_loan_amt)
                m.max_loan_amt = Decimal(max_loan_amt)
                m.premium = Decimal(premium)

                m.save()

            self.stdout.write('\nSuccessfully loaded data from %s\n\n' % filename)

    def load_upfront(self, filename):
        with open(filename, 'rU') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')

            # Delete all items in tables
            Upfront.objects.all().delete()

            # Remove the first line which is the header line
            csvreader.next()

            for row in csvreader:

                loan_type, va_status, va_first_use, min_ltv, max_ltv, premium = row

                u = Upfront()
                
                u.loan_type = loan_type.strip().upper()
                u.va_status = va_status.strip().upper()
                u.va_first_use = va_first_use.strip().upper()
                u.min_ltv = Decimal(min_ltv)
                u.max_ltv = Decimal(max_ltv)
                u.premium = Decimal(premium)

                u.save()

            self.stdout.write('\nSuccessfully loaded data from %s\n\n' % filename)
