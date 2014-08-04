from django.core.management.base import BaseCommand, CommandError
from countylimits.models import State, County, CountyLimit

import os
import sys
import xlrd

# from http://www.50states.com/abbreviations.htm
abbr_to_name = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado',
    'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana',
    'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota',
    'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
    'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming', 'AS': 'American Samoa', 'DC': 'District of Columbia',
    'FM': 'Federated States of Micronesia', 'GU': 'Guam', 'MH': 'Marshall Islands', 'MP': 'Northern Mariana Islands',
    'PW': 'Palau', 'PR': 'Puerto Rico', 'VI': 'Virgin Islands', 'AE': 'Armed Forces Africa', 'AA': 'Armed Forces Americas',
    'AE': 'Armed Forces Canada', 'AE': 'Armed Forces Europe', 'AE': 'Armed Forces Middle East', 'AP': 'Armed Forces Pacific',
}


class Command(BaseCommand):
    args = '<file_path>'
    help = 'Load county limits from an excel file.'

    def handle(self, *args, **options):
        self.stdout.write('\n------------------------------------------\n')
        self.stdout.write('\n1. Reads data from the first file worksheet only')
        self.stdout.write('2. First row is assumed to have column names, and is skipped while loading data')
        self.stdout.write('3. Assumed field order: State, State FIPS, County FIPS, Complete FIPS, County Name, GSE Limit, FHA Limit, VA Limit\n')
        self.stdout.write('\n------------------------------------------\n')
        for file_path in args:
            try:
                limits_file = xlrd.open_workbook(file_path)
                worksheet = limits_file.sheets()[0]
                states = {}
                counties = {}

                CountyLimit.objects.all().delete()
                County.objects.all().delete()
                State.objects.all().delete()

                for i in xrange(worksheet.nrows):
                    if not i:
                        continue
                    row = worksheet.row_values(i)
                    state, state_fips, county_fips, complete_fips, county, gse, fha, va = row
                    if state not in states:
                        s = State(state_abbr=state, state_fips=state_fips, state_name=abbr_to_name[state])
                        s.save()
                        states[state] = s.id

                    if complete_fips not in counties:
                        c = County(county_name=county, county_fips=county_fips, state_id=states[state])
                        c.save()
                        counties[complete_fips] = c.id

                    cl = CountyLimit(fha_limit=fha, gse_limit=gse, va_limit=va, county_id=counties[complete_fips])
                    cl.save()

            except IOError as ioe:
                raise CommandError('IOError: %s' % ioe)
            except xlrd.biffh.XLRDError as xlrde:
                raise CommandError('XLS Reader Error: %s' % xlrde)

            self.stdout.write('Successfully loaded data from %s' % file_path)
            break
        else:
            raise CommandError('A path to an excel county limits file is required')
