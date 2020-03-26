from django.core.management.base import BaseCommand

from countylimits.data_collection.gather_county_data import get_chums_data


COMMAND_HELP = "Gathers annaul county mortgage limit data from the "
"HUD website and processes it for use in the owning-a-home-api. "
"Processed source files are saved in the app's /data/base_data/ folder.  "
PARSER_HELP = "An optional '--year' value may be supplied to process "
"data files from a particular year. The default year value is the year after "
"the current year, because this script is normally run at the end of "
"December for the next year's values."


class Command(BaseCommand):
    help = COMMAND_HELP

    def add_arguments(self, parser):
        parser.add_argument("--year", help=PARSER_HELP, type=int)

    def handle(self, *args, **options):
        if options["year"]:
            msg = get_chums_data(year=options["year"])
        else:
            msg = get_chums_data()
        self.stdout.write(msg)
