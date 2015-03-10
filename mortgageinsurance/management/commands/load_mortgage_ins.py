from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from decimal import Decimal

import csv

# from mortgageinsurance.models import Insurance # Will update once we start implementing the models


class Command(BaseCommand):
    args = '<file_path>'
    help = 'Load mortgage insurance data from a CSV file.'
    option_list = BaseCommand.option_list + (
        make_option('--confirm', action='store', dest='confirmed', help='Confirm that you have read the comments'),
    )

    def handle(self, *args, **options):
        self.stdout.write('\n------------------------------------------\n')
        self.stdout.write('\n1. First row is assumed to have column names, and is skipped while loading data')
        self.stdout.write('\n2. Assumed field order: Mortgage Insurer, Min Loan To Value Ratio, Max Loan To Value Ratio, ' \
                          'Min FICO Score, Max FICO Score, Min Loan Term, Max Loan Term, Rate Type, Min Loan Amount, Max Loan Amount, Premium')
        self.stdout.write('\n3. All current data in mortgageinsurance_(x|x|x) tables will be deleted')
        self.stderr.write('\n If you read the above comments and agree, call the command with "--confirm=y" option\n')
        self.stdout.write('\n------------------------------------------\n')

        if 'confirmed' not in options or options['confirmed'].lower() != 'y':
            return

        if len(args) > 0:
            try:
                with open(args[0], 'rU') as csvfile:
                    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')

                    # Delete all items in tables
                    # MortgageInsurance.objects.all().delete()

                    is_first_row = True
                    for row in csvreader:

                        if is_first_row:
                            is_first_row = False
                            continue

                        insurer, min_ltv, max_ltv, min_fico, max_fico, min_loan_term, max_loan_term, pymt_type, min_loan_amt, max_loan_amt, premium = row

                        # self.stdout.write('\nrow: %s\n' % row)
                        # self.stdout.write('insurer:%s, minltv:%s, maxltv:%s, minfico:%s, maxfico:%s, min_loan_term:%s, max_loan_term:%s, rate_type:%s, min_loan_amt:%s, max_loan_amt:%s, premium:%s' % 
                        #                     (insurer, minltv, maxltv, minfico, maxfico, min_loan_term, max_loan_term, rate_type, min_loan_amt, max_loan_amt, premium))
                        m = MonthlyMortgageIns()
                        
                        m.insurer = insurer.strip()
                        m.min_ltv = Decimal(min_ltv)
                        m.max_ltv = Decimal(max_ltv)
                        m.min_fico = int(min_fico)
                        m.max_fico = int(max_fico)
                        m.min_loan_term = int(min_loan_term)
                        m.max_loan_term = int(max_loan_term)
                        m.pymt_type = pymt_type.strip()
                        m.min_loan_amt = Decimal(min_loan_amt)
                        m.max_loan_amt = Decimal(max_loan_amt)
                        m.premium = Decimal(premium)

                        m.save()

                        # m = MortgageInsurance(insurer=insurer, minltv=minltv, max_ltv=maxltv, minfico=minfico, maxfico=maxfico, 
                        #                       min_loan_term=min_loan_term, max_loan_term=max_loan_term, rate_type=rate_type, 
                        #                       min_loan_amt=min_loan_amt, max_loan_amt=max_loan_amt, premium=premium)

                        # m.save()

                self.stdout.write('\nSuccessfully loaded data from %s\n\n' % args[0])
            except IOError as e:
                raise CommandError(e)
        else:
            raise CommandError('A path to a CSV county limits file is required.')
