from django.db import models
from localflavor.us.models import USStateField
from localflavor.us.us_states import STATE_CHOICES


abbr_to_name = dict(STATE_CHOICES)

"""
We use Federal Information Processing Standard (FIPS) state and county codes.
More information can be found in the following articles:
http://en.wikipedia.org/wiki/Federal_Information_Processing_Standard_state_code
http://en.wikipedia.org/wiki/FIPS_county_code
"""


class State(models.Model):
    """ A basic State object. """
    state_fips = models.CharField(
        max_length=2, help_text='A two-digit FIPS code for the state')
    state_abbr = USStateField(help_text='A two-letter state abbreviation')

    class Meta:
        ordering = ['state_fips']

    def __unicode__(self):
        return u'%s' % abbr_to_name[self.state_abbr]


class County(models.Model):
    """ A basic state county object. """
    county_fips = models.CharField(
        max_length=3,
        help_text='A three-digit FIPS code for the state\'s county')
    county_name = models.CharField(max_length=100, help_text='The county name')
    state = models.ForeignKey(State)

    class Meta:
        ordering = ['county_fips']

    def __unicode__(self):
        return u'%s (%s)' % (self.county_name, self.county_fips)


class CountyLimit(models.Model):
    """ County limit object. """
    fha_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Federal Housing Administration '
                  'loan lending limit for the county')
    gse_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Loan limit for mortgages acquired '
                  'by the Government-Sponsored Enterprises')
    va_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='The Department of Veterans Affairs '
                  'loan guaranty program limit')
    county = models.OneToOneField(County)

    def __unicode__(self):
        return u'CountyLimit %s' % self.id

    @staticmethod
    def county_limits_by_state(state):
        """ Get a list of state counties with limits. """
        data = []
        # state value can be a State FIPS or a state abbr.
        state_obj = State.objects.filter(
            models.Q(state_fips=state) |
            models.Q(state_abbr=state)).first()
        limits = CountyLimit.objects.filter(county__state=state_obj)
        for countylimit in limits:
            data.append(
                {u'state': unicode(abbr_to_name[state_obj.state_abbr]),
                 u'county': countylimit.county.county_name,
                 u'complete_fips': u'{}{}'.format(
                     state_obj.state_fips,
                     countylimit.county.county_fips),
                 u'gse_limit': unicode(countylimit.gse_limit),
                 u'fha_limit': unicode(countylimit.fha_limit),
                 u'va_limit': unicode(countylimit.va_limit)}
            )
        return data
