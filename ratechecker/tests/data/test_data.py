import os
from datetime import date

from django.test import TestCase

from ratechecker.dataset import Dataset
from ratechecker.models import Product


SAMPLE_DATASET_FILENAME = os.path.abspath(
    os.path.join(__file__, "../../../data/sample.zip")
)


class TestDataset(TestCase):
    def setUp(self):
        self.expected_date = date(2017, 3, 2)

    def test_load_date(self):
        with open(SAMPLE_DATASET_FILENAME, "rb") as f:
            d = Dataset(f)
            self.assertEqual(d.cover_sheet.date, self.expected_date)

    def test_load_products(self):
        with open(SAMPLE_DATASET_FILENAME, "rb") as f:
            Dataset(f).load()
            self.assertTrue(Product.objects.exists())

    def test_load_products_timestamp(self):
        with open(SAMPLE_DATASET_FILENAME, "rb") as f:
            dataset = Dataset(f)
            dataset.load()
            self.assertEqual(
                Product.objects.first().data_timestamp, dataset.timestamp
            )
