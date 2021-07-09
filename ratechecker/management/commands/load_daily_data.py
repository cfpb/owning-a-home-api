import argparse
import traceback
import warnings

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from ratechecker.dataset import Dataset
from ratechecker.validation import ScenarioValidator


class Command(BaseCommand):
    help = "Loads daily interest rate data from a zip archive with CSV files."

    def add_arguments(self, parser):
        parser.add_argument(
            "archive_filename",
            type=argparse.FileType("rb"),
            help="Archive containing interest rate data",
        )
        parser.add_argument(
            "-s",
            "--validation-scenario-file",
            type=argparse.FileType("r"),
            help="JSON-line file containing validation scenario parameters",
        )
        parser.add_argument(
            "--validate-only",
            action="store_true",
            help="Skip load and revalidate existing table",
        )

    def handle(self, **options):
        warnings.filterwarnings("ignore", "Unknown table.*")
        self.verbosity = options["verbosity"]

        archive = options["archive_filename"]
        validate_only = options["validate_only"]
        validation_file = options.get("validation_scenario_file")

        if not validate_only:
            self.print("Copying data to temp tables")
            self.archive_data_to_temp_tables()

        try:
            self.print("Loading data from", archive.name)
            dataset = Dataset(archive)

            if not validate_only:
                self.print("Loading dataset with timestamp", dataset.timestamp)
                dataset.load()

            if validation_file:
                self.print("Validating loaded data with", validation_file.name)
                validator = ScenarioValidator(verbose=self.verbosity)
                validator.validate_file(validation_file, dataset)
        except Exception:
            self.print(traceback.format_exc())

            if not validate_only:
                self.print("Restoring old data")

                self.delete_data_from_base_tables()
                self.reload_old_data()

            raise CommandError("Load failed")
        finally:
            if not validate_only:
                self.print("Cleaning up temp tables")
                self.delete_temp_tables()

        self.print("Load successful")

    def print(self, *args, **kwargs):
        if self.verbosity:  # pragma: no cover
            print(*args, **kwargs)

    def archive_data_to_temp_tables(self):
        """Save data to temporary tables and delete it from normal tables."""
        self.delete_temp_tables()

        cursor = connection.cursor()
        cursor.execute(
            "CREATE TABLE temporary_product AS "
            "SELECT * FROM ratechecker_product"
        )
        cursor.execute(
            "CREATE TABLE temporary_region AS "
            "SELECT * FROM ratechecker_region"
        )
        cursor.execute(
            "CREATE TABLE temporary_rate AS " "SELECT * FROM ratechecker_rate"
        )
        cursor.execute(
            "CREATE TABLE temporary_adjustment AS "
            "SELECT * FROM ratechecker_adjustment"
        )

        self.delete_data_from_base_tables()

    def delete_temp_tables(self):
        """Delete temporary tables."""
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS temporary_product")
        cursor.execute("DROP TABLE IF EXISTS temporary_region")
        cursor.execute("DROP TABLE IF EXISTS temporary_rate")
        cursor.execute("DROP TABLE IF EXISTS temporary_adjustment")

    def delete_data_from_base_tables(self):
        """Delete current data."""
        cursor = connection.cursor()
        cursor.execute("DELETE FROM ratechecker_product")
        cursor.execute("DELETE FROM ratechecker_region")
        cursor.execute("DELETE FROM ratechecker_rate")
        cursor.execute("DELETE FROM ratechecker_adjustment")

    def reload_old_data(self):
        """Move data from temporary tables back into the base tables."""
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO ratechecker_product "
            "SELECT * FROM temporary_product"
        )
        cursor.execute(
            "INSERT INTO ratechecker_adjustment "
            "SELECT * FROM temporary_adjustment"
        )
        cursor.execute(
            "INSERT INTO ratechecker_rate " "SELECT * FROM temporary_rate"
        )
        cursor.execute(
            "INSERT INTO ratechecker_region " "SELECT * FROM temporary_region"
        )
