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
    loan_term = models.IntegerField(help_text='loan term')
    pmt_type = models.CharField(max_length=12, choices=PAYMENT_TYPE_CHOICES, help_text='Rate Type')
    min_loan_amt = models.DecimalField(max_digits=12, decimal_places=2, help_text='Minimum loan amount')
    max_loan_amt = models.DecimalField(max_digits=12, decimal_places=2, help_text='Maximum loan amount')
    premium = models.DecimalField(max_digits=6, decimal_places=3, help_text='Premium')

    def __unicode__(self):
        return u'%s ltv: (%s %s) fico: (%s %s) loan term: (%s) %s loan amount: (%s %s) Premium: %s' % \
                (self.insurer, self.min_ltv, self.max_ltv, self.min_fico, self.max_fico, self.loan_term, 
                    self.pmt_type, self.min_loan_amt, self.max_loan_amt, self.premium)

    @staticmethod
    def get_avg_premium(params_data):
        result = {}
        avg_premium = 0.0

        ltv = ((params_data['loan_amount'] / params_data['price']) * 100).quantize(Decimal('.001'), rounding=ROUND_HALF_UP)

        if params_data['loan_type'] in (Monthly.FHA, Monthly.FHA_HB) :
            q_insurer = Q(insurer=Monthly.FHA)
        else:
            q_insurer = ~Q(insurer=Monthly.FHA)

        result = Monthly.objects.filter(
            q_insurer &
            Q(min_ltv__lte=ltv) & 
            Q(max_ltv__gte=ltv) &
            Q(min_fico__lte=params_data['minfico']) & 
            Q(max_fico__gte=params_data['minfico']) &
            Q(min_fico__lte=params_data['maxfico']) & 
            Q(max_fico__gte=params_data['maxfico']) &
            Q(loan_term=params_data['loan_term']) & 
            Q(pmt_type=params_data['rate_structure']) &
            Q(min_loan_amt__lte=params_data['loan_amount']) & 
            Q(max_loan_amt__gte=params_data['loan_amount'])).aggregate(Avg('premium'))

        avg_premium = 0.0 if result['premium__avg'] is None else round(result['premium__avg'], 3)

        return avg_premium

class Upfront(models.Model):


    DISABLED = 'DISABLED'
    REGULAR = 'REGULAR'
    RES_NG = 'RES-NG'

    VA_STATUS_CHOICES = (
        (DISABLED, 'Veteran with Disability'),
        (REGULAR, 'Regular'),
        (RES_NG, 'Reserve or National Guard'),
    )

    YES = 'Y'
    NO = 'N'

    VA_1ST_USE_CHOICES = (
        (YES, "Yes, First Time Use"),
        (NO, "No, Not First Time Use")
    )
    loan_type = models.CharField(max_length=12, choices=Monthly.LOAN_TYPE_CHOICES, help_text='Loan Type')
    va_status = models.CharField(max_length=12, choices=VA_STATUS_CHOICES, blank=True, help_text='VA Status')
    va_first_use = models.CharField(max_length=3, choices=VA_1ST_USE_CHOICES, blank=True, help_text='VA First Time Use')
    min_ltv = models.DecimalField(max_digits=6, decimal_places=3, help_text='Minimum loan to value ratio')
    max_ltv = models.DecimalField(max_digits=6, decimal_places=3, help_text='Maximum loan to value ratio')
    premium = models.DecimalField(max_digits=6, decimal_places=3, help_text='Premium')

    def __unicode__(self):
        return u'%s va status: (%s), va first use? (%s) ltv: (%s %s) Premium: %s' % \
                (self.loan_type, self.va_status, self.va_first_use, self.min_ltv, 
                    self.max_ltv, self.premium)

    @staticmethod
    def get_premium(params_data):
        result = {}
        premium = 0.0

        ltv = ((params_data['loan_amount'] / params_data['price']) * 100).quantize(Decimal('.001'), rounding=ROUND_HALF_UP)

        if params_data['loan_type'] in (Monthly.FHA, Monthly.FHA_HB):
            result = Upfront.objects.get(
                Q(loan_type=Monthly.FHA) &
                Q(min_ltv__lte=ltv) & 
                Q(max_ltv__gte=ltv))

        elif params_data['loan_type'] in (Monthly.VA, Monthly.VA_HB) :

            if params_data['va_status'] == Upfront.DISABLED:
                result = Upfront.objects.get(
                    Q(loan_type=Monthly.VA) &
                    Q(va_status=Upfront.DISABLED) &
                    Q(min_ltv__lte=ltv) & 
                    Q(max_ltv__gte=ltv))
            else :
                result = Upfront.objects.get(
                    Q(loan_type=Monthly.VA) &
                    Q(va_status=params_data['va_status']) &
                    Q(va_first_use=params_data['va_first_use']) &
                    Q(min_ltv__lte=ltv) & 
                    Q(max_ltv__gte=ltv))

        premium = 0.0 if result is None or result.premium is None else round(result.premium, 3)

        return premium
