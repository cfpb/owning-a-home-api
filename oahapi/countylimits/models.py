from django.db import models
from localflavor.us.models import USStateField
from localflavor.us.us_states import STATE_CHOICES

abbr_to_name = dict(STATE_CHOICES)


class State(models.Model):
    """ A basic State object. """
    state_fips = models.CharField(max_length=2)
    state_abbr = USStateField()

    def __unicode__(self):
        return u'%s' % self.state_name


class County(models.Model):
    """ A basic state county object. """
    county_fips = models.CharField(max_length=3)
    county_name = models.CharField(max_length=100)
    state = models.ForeignKey(State)

    def __unicode__(self):
        return u'%s (%s)' % (self.county_name, self.county_fips)


class CountyLimit(models.Model):
    """ County limit object. """
    fha_limit = models.DecimalField(max_digits=12, decimal_places=2)
    gse_limit = models.DecimalField(max_digits=12, decimal_places=2)
    va_limit = models.DecimalField(max_digits=12, decimal_places=2)
    county = models.OneToOneField(County)

    def __unicode__(self):
        return u'CountyLimit %s' % self.id

    @staticmethod
    def county_limits_by_state(state):
        """ Get a list of state counties with limits. """
        data = []
        try:
            # state value can be a State FIPS or a state abbr.
            result = CountyLimit.objects.filter(models.Q(county__state__state_fips=state) | models.Q(county__state__state_abbr=state))
            for countylimit in result:
                data.append({
                    'state': abbr_to_name[countylimit.county.state.state_abbr],
                    'county': countylimit.county.county_name,
                    'complete_fips': '%s%s' % (countylimit.county.state.state_fips, countylimit.county.county_fips),
                    'gse_limit': countylimit.gse_limit,
                    'fha_limit': countylimit.fha_limit,
                    'va_limit': countylimit.va_limit,
                })
        except:
            pass
        return data
