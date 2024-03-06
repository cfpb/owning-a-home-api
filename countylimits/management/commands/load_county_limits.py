import csv
import sys

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from countylimits.models import County, CountyLimit, State


DEFAULT_COUNTYLIMIT_FIXTURE = "countylimit_data.json"
DEFAULT_CSV = {"latest": "countylimits/data/county_limit_data_latest.csv"}


def dump_countylimit_fixture(to_filename=None):
    filename = to_filename or "countylimits/fixtures/{}".format(
        DEFAULT_COUNTYLIMIT_FIXTURE
    )

    sysout = sys.stdout
    with open(filename, "w") as sys.stdout:
        call_command("dumpdata", "countylimits")
        sys.stdout = sysout


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--csv", dest="csv", type=str, help="File path to CSV to load"
        )

        parser.add_argument(
            "--confirm",
            dest="confirmed",
            help="Confirm that you have read the comments",
        )

        parser.add_argument(
            "--dumpdata",
            dest="dumpdata",
            default="false",
            help=(
                "load_county_limits via CSV will dump a fixture "
                'if "--dumpdata=true" is set'
            ),
        )

    def handle(self, *args, **options):
        self.stdout.write("\n------------------------------------------\n")
        self.stdout.write("\nIf loading a CSV, there are 3 things to know:\n")
        self.stdout.write(
            "1. You can pass in a path, or `latest` to load the latest CSV\n"
            "   Passing `--csv=latest` is the same as passing:\n"
            "   `--csv=countylimits/data/county_limit_data_latest.csv`"
        )
        self.stdout.write(
            "2. The CSV's first row is assumed to be the column names, "
            "and it is skipped when loading data"
        )
        self.stdout.write(
            "3. This field order is assumed: \n"
            "    State,\n"
            "    State FIPS,\n"
            "    County FIPS,\n"
            "    Complete FIPS,\n"
            "    County Name,\n"
            "    GSE Limit,\n"
            "    FHA Limit,\n"
            "    VA Limit\n"
        )
        self.stdout.write(
            "\nAlso Note:\n"
            "- All current data will be deleted from these "
            "tables: countylimits_(state|county|countylimit)"
        )
        self.stdout.write(
            "- If you provide no `--csv` argument, data will be "
            "loaded from the `countylimit_data.json` fixture\n"
        )
        self.stdout.write(
            "- If you provide both `--csv=latest` and `--dumpdata=true`,"
            "the loaded CSV data will dumped as `countylimit_data.json`\n"
        )
        self.stderr.write(
            "\n If you read the above comments and agree, "
            'call your command again with the "--confirm=y" option\n'
        )
        self.stdout.write("\n------------------------------------------\n")

        if not options.get("confirmed") or options["confirmed"].lower() != "y":
            return

        if options.get("csv"):
            # Users can pass in `latest` or their own CSV path
            csv_file = DEFAULT_CSV.get(options.get("csv"), options.get("csv"))
            try:
                with open(csv_file, "r", newline="") as csvfile:
                    csvreader = csv.reader(
                        csvfile, delimiter=",", quotechar='"'
                    )
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
                        (
                            state,
                            state_fips,
                            county_fips,
                            complete_fips,
                            county,
                            gse,
                            fha,
                            va,
                        ) = row
                        if state not in states:
                            s = State(state_abbr=state, state_fips=state_fips)
                            s.save()
                            states[state] = s.id

                        if complete_fips not in counties:
                            c = County(
                                county_name=county,
                                county_fips=county_fips,
                                state_id=states[state],
                            )
                            c.save()
                            counties[complete_fips] = c.id

                        cl = CountyLimit(
                            fha_limit=fha,
                            gse_limit=gse,
                            va_limit=va,
                            county_id=counties[complete_fips],
                        )
                        cl.save()
                self.stdout.write(
                    "\nSuccessfully loaded data for {} counties from "
                    "{}\n\n".format(CountyLimit.objects.count(), csv_file)
                )
                if options.get("dumpdata") == "true":
                    dump_countylimit_fixture()
            except IOError as e:
                raise CommandError(e)
        else:
            CountyLimit.objects.all().delete()
            County.objects.all().delete()
            State.objects.all().delete()
            call_command(
                "loaddata",
                DEFAULT_COUNTYLIMIT_FIXTURE,
                app_label="countylimits",
            )
            self.stdout.write(
                "\nSuccessfully loaded data for {} counties from {}".format(
                    CountyLimit.objects.count(), DEFAULT_COUNTYLIMIT_FIXTURE
                )
            )
