from csv import reader
import os
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = "<directory_path>"
    help = """ Loads daily interest rate data from CSV files.
        All files are in one directory. """

    def get_date_from_filename(self, file_name):
        """ The data corresponding to the data is part of the filename. We
        extract that here. """

        for dstr in file_name.split('_'):
            try:
                file_date = datetime.strptime(dstr, '%Y%m%d')
                return file_date 
            except ValueError:
                pass
        raise ValueError('No date in filename')


    def get_data_file_paths(self, directory_name):
        """ Get the files paths and some metadata about the data load.  We try
        not to assume too much about the data file names at this point.  """

        data = {}
        data_files = {}

        for root, dirs, files in os.walk(directory_name):
            for name in files:
                if 'product' in name:
                    data_files['product'] = name
                elif 'region' in name:
                    data_files['region'] = name
                elif 'rate' in name:
                    data_files['rate'] = name
                elif 'adjustment' in name:
                    data_files['adjustment'] = name 
        data_date = self.get_date_from_filename(data_files['product'])

        data['date'] = data_date
        data['file_names'] = data_files
        return data

    def handle(self, *args, **options):
        """ Given a directory containing the days files, this command will load
        all the data for that day. """

        data_information = self.get_data_file_paths(args[0])

        self.load_product_data(
            data_information['date'],
            data_information['file_names']['product']])
