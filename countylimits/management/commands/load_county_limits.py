from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import sys

import csv

from countylimits.models import State, County, CountyLimit

DEFAULT_COUNTYLIMIT_FIXTURE = 'countylimit_data.json'


class Command(BaseCommand):
    args = '<file_path>'
    help = 'Load county limits from a CSV file.'
    option_list = BaseCommand.option_list + (
        make_option('--confirm',
                    action='store',
                    dest='confirmed',
                    help='Confirm that you have read the comments'),
    )

    def handle(self, *args, **options):
        self.stdout.write('\n------------------------------------------\n')
        self.stdout.write('\nIf loading a CSV, there are 3 requirements:\n')
        self.stdout.write('1. Pass in a relative path to the CSV, such as \n'
                          'countylimits/data/county_limit_data_latest.csv')
        self.stdout.write("2. The CSV's first row is assumed to be "
                          "column names, and is skipped when loading data")
        self.stdout.write('3. This field order is assumed: \n'
                          '  State,\n'
                          '  State FIPS,\n'
                          '  County FIPS,\n'
                          '  Complete FIPS,\n'
                          '  County Name,\n'
                          '  GSE Limit,\n'
                          '  FHA Limit,\n'
                          '  VA Limit\n')
        self.stdout.write('\nAlso Note:\n'
                          '- All current data will be deleted from these '
                          'tables: countylimits_(state|county|countylimit)')
        self.stdout.write('- If you provide no path to a CSV, data will be '
                          'loaded from the `countylimit_data.json` fixture\n')
        self.stderr.write('\n If you read the above comments and agree, '
                          'call the command again with "--confirm=y" option\n')
        self.stdout.write('\n------------------------------------------\n')

        if not options.get('confirmed') or options['confirmed'].lower() != 'y':
            return

        if len(args) > 0:
            try:
                with open(args[0], 'rU') as csvfile:
                    csvreader = csv.reader(
                        csvfile, delimiter=',', quotechar='"')
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
                        (state, state_fips, county_fips,
                         complete_fips, county, gse, fha, va) = row
                        if state not in states:
                            s = State(state_abbr=state, state_fips=state_fips)
                            s.save()
                            states[state] = s.id

                        if complete_fips not in counties:
                            c = County(
                                county_name=county,
                                county_fips=county_fips,
                                state_id=states[state]
                            )
                            c.save()
                            counties[complete_fips] = c.id

                        cl = CountyLimit(
                            fha_limit=fha,
                            gse_limit=gse,
                            va_limit=va,
                            county_id=counties[complete_fips]
                        )
                        cl.save()

                sysout = sys.stdout
                with open('countylimits/fixtures/{}'.format(
                        DEFAULT_COUNTYLIMIT_FIXTURE), 'w') as sys.stdout:
                    call_command('dumpdata', 'countylimits')
                    sys.stdout = sysout
                self.stdout.write(
                    '\nSuccessfully loaded data from {}\n\n'.format(args[0])
                )
            except IOError as e:
                raise CommandError(e)
        else:
            CountyLimit.objects.all().delete()
            County.objects.all().delete()
            State.objects.all().delete()
            call_command(
                'loaddata',
                DEFAULT_COUNTYLIMIT_FIXTURE,
                app_label='countylimits')
            self.stdout.write(
                '\nSuccessfully loaded data from {}'.format(
                    DEFAULT_COUNTYLIMIT_FIXTURE)
            )
