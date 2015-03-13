from django.db import models
from django.db.models import Q, Avg
from decimal import *


class MonthlyMortgageIns(models.Model):

    FIXED = 'FIXED'
    ARM = 'ARM'

    PAYMENT_TYPE_CHOICES = (
        (FIXED, 'Fixed Rate Mortgage'),
        (ARM, 'Adjustable Rate Mortgage'))

    JUMBO = 'JUMBO'
    CONF = 'CONF'
    AGENCY = 'AGENCY'
    FHA = 'FHA'
    VA = 'VA'
    VA_HB = 'VA-HB'
    FHA_HB = 'FHA-HB'

    LOAN_TYPE_CHOICES = (
        (JUMBO, 'Jumbo Mortgage'),
        (CONF, 'Conforming Loan'),
        (AGENCY, 'Agency Loan'),
        (FHA, 'Federal Housing Administration Loan'),
        (VA, 'Veterans Affairs Loan'),
        (VA_HB, 'VA-HB Loan'),
        (FHA_HB, 'FHA-HB Loan'),
    )

    insurer = models.CharField(max_length=200, help_text='Abbreviation of the mortgage insurer')
    min_ltv = models.DecimalField(max_digits=6, decimal_places=3, help_text='Minimum loan to value ratio')
    max_ltv = models.DecimalField(max_digits=6, decimal_places=3, help_text='Maximum loan to value ratio')
    min_fico = models.IntegerField(help_text='Minimum FICO score')
    max_fico = models.IntegerField(help_text='Maximum FICO score')
    min_loan_term = models.DecimalField(max_digits=6, decimal_places=3, help_text='Minimum loan term')
    max_loan_term = models.DecimalField(max_digits=6, decimal_places=3, help_text='Maximum loan term')
    pmt_type = models.CharField(max_length=12, choices=PAYMENT_TYPE_CHOICES, help_text='Rate Type')
    min_loan_amt = models.DecimalField(max_digits=12, decimal_places=2, help_text='Minimum loan amount')
    max_loan_amt = models.DecimalField(max_digits=12, decimal_places=2, help_text='Maximum loan amount')
    premium = models.DecimalField(max_digits=5, decimal_places=2, help_text='Premium')

    def __unicode__(self):
        return u'%s ltv: (%s %s) fico: (%s %s) loan term: (%s %s) %s loan amount: (%s %s) Premium: %s' % \
                (self.insurer, self.min_ltv, self.max_ltv, self.min_fico, self.max_fico, self.min_loan_term, 
                    self.max_loan_term, self.pmt_type, self.min_loan_amt, self.max_loan_amt, self.premium)

    @staticmethod
    def get_avg_premium(params_data):
        avg_premium = 0.0

        ltv = ((params_data['loan_amount'] / params_data['price']) * 100).quantize(Decimal('.001'), rounding=ROUND_HALF_UP)

        print 'ltv:'
        print ltv

        # If loan type is VA/ VA_HB, 
        if params_data['loan_type'] in (MonthlyMortgageIns.VA, MonthlyMortgageIns.VA_HB) :
            result = MonthlyMortgageIns.objects.filter(
                Q(insurer=MonthlyMortgageIns.VA) &
                Q(min_ltv__lte=ltv) & 
                Q(max_ltv__gte=ltv) &
                Q(min_fico__lte=params_data['minfico']) & 
                Q(max_fico__gte=params_data['minfico']) &
                Q(min_fico__lte=params_data['maxfico']) & 
                Q(max_fico__gte=params_data['maxfico']) &
                Q(min_loan_term__lte=params_data['loan_term']) & 
                Q(max_loan_term__gte=params_data['loan_term']) &
                Q(pmt_type=params_data['rate_structure']) &
                Q(min_loan_amt__lte=params_data['loan_amount']) & 
                Q(max_loan_amt__gte=params_data['loan_amount'])).aggregate(Avg('premium'))

            # print 'query:'
            # print result.query
            print 'avg premium: '
            print result
            avg_premium = 0.0 if result['premium__avg'] is None else round(result['premium__avg'], 3)
        else :
            result = MonthlyMortgageIns.objects.filter(
                ~Q(insurer=MonthlyMortgageIns.VA) &
                Q(min_ltv__lte=ltv) & Q(max_ltv__gte=ltv) &
                Q(min_fico__lte=params_data['minfico']) & 
                Q(max_fico__gte=params_data['minfico']) &
                Q(min_fico__lte=params_data['maxfico']) & 
                Q(max_fico__gte=params_data['maxfico']) &
                Q(min_loan_term__lte=params_data['loan_term']) & 
                Q(max_loan_term__gte=params_data['loan_term']) &
                Q(pmt_type=params_data['rate_structure']) &
                Q(min_loan_amt__lte=params_data['loan_amount']) & 
                Q(max_loan_amt__gte=params_data['loan_amount'])).aggregate(Avg('premium'))

            # print 'query:'
            # print result.query
            # print 'query:'
            # print result.query
            print 'avg premium: '
            print result
            avg_premium = 0.0 if result['premium__avg'] is None else round(result['premium__avg'], 3)
        # select * from monthlymortgageins where 
        # insurer = VA, 
        # ltv between min_ltv and max_ltv,
        # minfico is > minfico and < maxfico
        # maxfico is < maxfico and > maxfico
        # loan_term > min_loan_term and < max_loan_term
        # pmt_type = pmt_type
        # loan_amt > min_loan_amt and < max_loan_amount
        # else
        # select * from monthlymortgageins where
        # insurer != VA
        # ltv between min_ltv and max_ltv,
        # minfico is > minfico and < maxfico
        # maxfico is < maxfico and > maxfico
        # loan_term > min_loan_term and < max_loan_term
        # pmt_type = pmt_type
        # loan_amt > min_loan_amt and < max_loan_amount

        # do an average on all the premium, then return
        return avg_premium
