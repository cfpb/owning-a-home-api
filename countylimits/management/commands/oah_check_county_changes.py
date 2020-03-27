from django.core.management.base import BaseCommand

from countylimits.data_collection.county_data_monitor import (  # noqa
    check_for_county_changes,
)


COMMAND_HELP = "Check the census county changelog against a local copy "
"of the last log to see whether updates have been added. "
"If changes are detected, send an email alert about the change "
"and update our local 'last_changelog.txt' file."
PARSER_HELP = "This command accepts a space-separated string "
"of email recipients who will be notified if county changes are detected."


class Command(BaseCommand):
    help = COMMAND_HELP

    def add_arguments(self, parser):
        parser.add_argument("--email", help=PARSER_HELP, nargs="+", type=str)

    def handle(self, *args, **options):
        if options["email"]:
            msg = check_for_county_changes(email=options["email"])
        else:
            msg = check_for_county_changes()
        self.stdout.write(msg)
