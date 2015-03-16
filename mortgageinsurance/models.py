from django.db import models
from django.db.models import Q, Avg
from decimal import *


class Monthly(models.Model):

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
        result = {}
        avg_premium = 0.0

        ltv = ((params_data['loan_amount'] / params_data['price']) * 100).quantize(Decimal('.001'), rounding=ROUND_HALF_UP)

        if params_data['loan_type'] in (Monthly.VA, Monthly.VA_HB) :
            q_insurer = Q(insurer=Monthly.VA)
        else:
            q_insurer = ~Q(insurer=Monthly.VA)

        result = Monthly.objects.filter(
            q_insurer &
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

        avg_premium = 0.0 if result['premium__avg'] is None else Decimal(str(result['premium__avg'])).quantize(Decimal('.001'), rounding=ROUND_HALF_UP)

        return avg_premium
