from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

import csv

from countylimits.models import State, County, CountyLimit


class Command(BaseCommand):
    args = '<file_path>'
    help = 'Load county limits from a CSV file.'
    option_list = BaseCommand.option_list + (
        make_option('--confirm', action='store', dest='confirmed', help='Confirm that you have read the comments'),
    )

    def handle(self, *args, **options):
        self.stdout.write('\n------------------------------------------\n')
        self.stdout.write('\n1. First row is assumed to have column names, and is skipped while loading data')
        self.stdout.write('\n2. Assumed field order: State, State FIPS, County FIPS, Complete FIPS, County Name, GSE Limit, FHA Limit, VA Limit')
        self.stdout.write('\n3. All current data in countylimits_(state|county|countylimit) tables will be deleted')
        self.stderr.write('\n If you read the above comments and agree, call the command with "--confirm=y" option\n')
        self.stdout.write('\n------------------------------------------\n')

        if not options.get('confirmed') or options['confirmed'].lower() != 'y':
            return

        if len(args) > 0:
            try:
                with open(args[0], 'rU') as csvfile:
                    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                    states = {}
                    counties = {}

                    CountyLimit.objects.all().delete()
                    County.objects.all().delete()
                    State.objects.all().delete()

                    i = 0
                    for row in csvreader:
                        if i == 0:
                            i += 1
                            continue
                        state, state_fips, county_fips, complete_fips, county, gse, fha, va = row
                        if state not in states:
                            s = State(state_abbr=state, state_fips=state_fips)
                            s.save()
                            states[state] = s.id

                        if complete_fips not in counties:
                            c = County(county_name=county, county_fips=county_fips, state_id=states[state])
                            c.save()
                            counties[complete_fips] = c.id

                        cl = CountyLimit(fha_limit=fha, gse_limit=gse, va_limit=va, county_id=counties[complete_fips])
                        cl.save()

                self.stdout.write('\nSuccessfully loaded data from %s\n\n' % args[0])
            except IOError as e:
                raise CommandError(e)
        else:
            raise CommandError('A path to a CSV county limits file is required.')
