import os
import shutil

from decimal import Decimal
from django.test import TestCase

from django.core.management import call_command
from django.utils.six import StringIO

from django.core.management.base import CommandError
from mortgageinsurance.management.commands.load_mortgage_insurance import Command
from mortgageinsurance.models import Monthly, Upfront

class LoadMortgageInsuranceTestCase(TestCase):

    def setUp(self):
        self.test_dir = '%s/test_folder' % os.path.dirname(os.path.realpath(__file__))

        os.mkdir(self.test_dir)
        os.chdir(self.test_dir)

        self.monthly_filename = 'mtg_ins_monthly_data.csv'
        self.prepare_monthly_sample_data(self.monthly_filename)
        self.upfront_filename = 'mtg_ins_upfront_data.csv'
        self.prepare_upfront_sample_data(self.upfront_filename)
        self.out = StringIO()

    def tearDown(self):
        """ Delete the test_folder dir."""
        shutil.rmtree(self.test_dir)

    def prepare_monthly_sample_data(self, filename):
        """ solely for test_load_monthly """
        with open(filename, 'w') as data:
            data.write("Header to be skipped\n")
            data.write("INS1,30.001,70,700,740,30,FIXED,400000,1000000,1.4\n")
            data.write("FHA,20.001,80,690,750,15,FIXED,200000,1200000,2.5\n")
            data.close()
            
    def prepare_upfront_sample_data(self, filename):
        """ solely for test_load_upfront """
        with open(filename, 'w') as data:
            data.write("Header to be skipped\n")
            data.write("FHA,,,0,80,3.75\n")
            data.write("VA,DISABLED,,4,70,1.5\n")
            data.write("VA,REGULAR,Y,3,75,2.0\n")
            data.close()

    def assert_monthly(self):
        m = Monthly.objects.all()
        self.assertEqual(len(m), 2)
        self.assertEqual(m[0].insurer, "INS1")
        self.assertEqual(m[0].min_ltv, Decimal("30.001"))
        self.assertEqual(m[0].max_ltv, Decimal("70"))
        self.assertEqual(m[0].min_fico, 700)
        self.assertEqual(m[0].max_fico, 740)
        self.assertEqual(m[0].loan_term, 30)
        self.assertEqual(m[0].pmt_type, "FIXED")
        self.assertEqual(m[0].min_loan_amt, Decimal("400000"))
        self.assertEqual(m[0].max_loan_amt, Decimal("1000000"))
        self.assertEqual(m[0].premium, Decimal("1.4"))
        self.assertEqual(m[1].insurer, "FHA")
        self.assertEqual(m[1].min_ltv, Decimal("20.001"))
        self.assertEqual(m[1].max_ltv, Decimal("80"))
        self.assertEqual(m[1].min_fico, 690)
        self.assertEqual(m[1].max_fico, 750)
        self.assertEqual(m[1].loan_term, 15)
        self.assertEqual(m[1].pmt_type, "FIXED")
        self.assertEqual(m[1].min_loan_amt, Decimal("200000"))
        self.assertEqual(m[1].max_loan_amt, Decimal("1200000"))
        self.assertEqual(m[1].premium, Decimal("2.5"))

    def assert_upfront(self):
        u = Upfront.objects.all()
        self.assertEqual(len(u), 3)
        self.assertEqual(u[0].loan_type, "FHA")
        self.assertEqual(u[0].va_status, "")
        self.assertEqual(u[0].va_first_use, None)
        self.assertEqual(u[0].min_ltv, Decimal("0"))
        self.assertEqual(u[0].max_ltv, Decimal("80"))
        self.assertEqual(u[0].premium, Decimal("3.75"))
        self.assertEqual(u[1].loan_type, "VA")
        self.assertEqual(u[1].va_status, "DISABLED")
        self.assertEqual(u[1].va_first_use, None)
        self.assertEqual(u[1].min_ltv, Decimal("4"))
        self.assertEqual(u[1].max_ltv, Decimal("70"))
        self.assertEqual(u[1].premium, Decimal("1.5"))
        self.assertEqual(u[2].loan_type, "VA")
        self.assertEqual(u[2].va_status, "REGULAR")
        self.assertEqual(u[2].va_first_use, 1)
        self.assertEqual(u[2].min_ltv, Decimal("3"))
        self.assertEqual(u[2].max_ltv, Decimal("75"))
        self.assertEqual(u[2].premium, Decimal("2.0"))


    def test_handle(self):
        """ Test normal handling """

        call_command('load_mortgage_insurance', self.monthly_filename, self.upfront_filename, confirmed='y', stdout=self.out)
        self.assertIn('Successfully', self.out.getvalue())

        m = Monthly.objects.all()
        u = Upfront.objects.all()
        self.assertEqual(len(m), 2)
        self.assert_monthly()
        self.assertEqual(len(u), 3)
        self.assert_upfront()

    def test_handle_upper_case_options(self):
        """ Test normal handling with upper case Y in options"""

        call_command('load_mortgage_insurance', self.monthly_filename, self.upfront_filename, confirmed='Y', stdout=self.out)
        self.assertIn('Successfully', self.out.getvalue())
        m = Monthly.objects.all()
        u = Upfront.objects.all()
        self.assertEqual(len(m), 2)
        self.assertEqual(len(u), 3)

    def test_handle_no_confirm(self):
        """ Test no confirm options handling """ 

        call_command('load_mortgage_insurance', self.monthly_filename, self.upfront_filename, stdout=self.out)
        self.assertNotIn('Successfully', self.out.getvalue())

        m = Monthly.objects.all()
        u = Upfront.objects.all()
        self.assertEqual(len(m), 0)
        self.assertEqual(len(u), 0)

    def test_handle_confirm_not_y(self):
        """ Test confirm option not equal y handling """ 

        call_command('load_mortgage_insurance', self.monthly_filename, self.upfront_filename, confirmed='n', stdout=self.out)
        self.assertNotIn('Successfully', self.out.getvalue())

        m = Monthly.objects.all()
        u = Upfront.objects.all()
        self.assertEqual(len(m), 0)
        self.assertEqual(len(u), 0)

    def test_handle_no_args(self):
        """ Test no arguments handling """ 
        self.assertRaises(CommandError, call_command, 'load_mortgage_insurance', confirmed='y', stdout=self.out)
        self.assertNotIn('Successfully', self.out.getvalue())

    def test_handle_one_args(self):
        """ Test with only one argument handling """ 
        self.assertRaises(CommandError, call_command, 'load_mortgage_insurance', self.monthly_filename, confirmed='y', stdout=self.out)
        self.assertNotIn('Successfully', self.out.getvalue())
