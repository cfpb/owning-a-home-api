from django.db import models

class MonthlyMortgageIns(models.Model):

    FIXED = 'FIXED'
    ARM = 'ARM'

    PAYMENT_TYPE_CHOICES = (
        (FIXED, 'Fixed Rate Mortgage'),
        (ARM, 'Adjustable Rate Mortgage'))

    insurer = models.CharField(max_length=200, help_text='Abbreviation of the mortgage insurer')
    min_ltv = models.DecimalField(max_digits=5, decimal_places=2, help_text='Minimum loan to value ratio')
    max_ltv = models.DecimalField(max_digits=5, decimal_places=2, help_text='Maximum loan to value ratio')
    min_fico = models.IntegerField(help_text='Minimum FICO score')
    max_fico = models.IntegerField(help_text='Maximum FICO score')
    min_loan_term = models.DecimalField(max_digits=5, decimal_places=2, help_text='Minimum loan term')
    max_loan_term = models.DecimalField(max_digits=5, decimal_places=2, help_text='Maximum loan term')
    pmt_type = models.CharField(max_length=12, choices=PAYMENT_TYPE_CHOICES, default=FIXED, help_text='Rate Type')
    min_loan_amt = models.DecimalField(max_digits=12, decimal_places=2, help_text='Minimum loan amount')
    max_loan_amt = models.DecimalField(max_digits=12, decimal_places=2, help_text='Maximum loan amount')
    premium = models.DecimalField(max_digits=5, decimal_places=2, help_text='Premium')

    def __unicode__(self):
        return u'%s ltv: (%s %s) fico: (%s %s) loan term: (%s %s) %s loan amount: (%s %s) Premium: %s' % \
                (self.insurer, self.min_ltv, self.max_ltv, self.min_fico, self.max_fico, self.min_loan_term, 
                    self.max_loan_term, self.pmt_type, self.min_loan_amt, self.max_loan_amt, self.premium)