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

    def __unicode__(self):
        return u'%s' % abbr_to_name[self.state_abbr]


class County(models.Model):
    """ A basic state county object. """
    county_fips = models.CharField(
        max_length=3,
        help_text='A three-digit FIPS code for the state\'s county')
    county_name = models.CharField(max_length=100, help_text='The county name')
    state = models.ForeignKey(State)

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
        result = County.objects.filter(
            models.Q(state__state_fips=state) |
            models.Q(state__state_abbr=state)
        )
        counties = {}
        state_abbr = ''
        state_fips = ''
        for county in result:
            if not state_abbr:
                state_abbr = county.state.state_abbr
                state_fips = county.state.state_fips
            counties[county.id] = {
                'county_name': county.county_name,
                'county_fips': county.county_fips
            }

        result = CountyLimit.objects.filter(
            models.Q(county__state__state_fips=state) |
            models.Q(county__state__state_abbr=state)
        )
        for countylimit in result:
            data.append(
                {'state': abbr_to_name[state_abbr],
                 'county': counties[countylimit.county_id]['county_name'],
                 'complete_fips': '{}{}'.format(
                    state_fips,
                    counties[countylimit.county_id]['county_fips']
                  ),
                 'gse_limit': countylimit.gse_limit,
                 'fha_limit': countylimit.fha_limit,
                 'va_limit': countylimit.va_limit}
            )
        return data
