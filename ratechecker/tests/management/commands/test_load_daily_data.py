import os
import shutil
import tempfile
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from ratechecker.tests.helpers import write_sample_dataset


class LoadDailyTestCase(TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def touch_file(self, f):
        with open(f, "a"):
            os.utime(f, None)

    def test_run_command_no_arguments(self):
        with self.assertRaises(CommandError):
            call_command("load_daily_data", verbosity=0)

    def test_run_command_invalid_filename(self):
        with self.assertRaises(CommandError):
            call_command("load_daily_data", "invalid-path", verbosity=0)

    @patch("ratechecker.loader.Loader.load")
    def test_run_command_invalid_scenario_file(self, _):
        archive_filename = os.path.join(self.tempdir, "archive.zip")
        write_sample_dataset(archive_filename)

        with self.assertRaises(CommandError):
            call_command(
                "load_daily_data",
                archive_filename,
                "--validation-scenario-file",
                "invalid.jsonl",
                verbosity=0,
            )

    @patch("ratechecker.loader.Loader.load")
    def test_run_command_calls_load(self, load):
        archive_filename = os.path.join(self.tempdir, "archive.zip")
        write_sample_dataset(archive_filename)

        validation_filename = os.path.join(self.tempdir, "scenarios.jsonl")
        self.touch_file(validation_filename)

        call_command(
            "load_daily_data",
            archive_filename,
            "--validation-scenario-file",
            validation_filename,
            verbosity=0,
        )
        self.assertEqual(load.call_count, 4)

    @patch("ratechecker.loader.Loader.load", side_effect=RuntimeError)
    def test_run_command_calls_load_handles_load_exception(self, load):
        archive_filename = os.path.join(self.tempdir, "archive.zip")
        write_sample_dataset(archive_filename)

        validation_filename = os.path.join(self.tempdir, "scenarios.jsonl")
        self.touch_file(validation_filename)

        with self.assertRaises(CommandError):
            call_command(
                "load_daily_data",
                archive_filename,
                "--validation-scenario-file",
                validation_filename,
                verbosity=0,
            )
