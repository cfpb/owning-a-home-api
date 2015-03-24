from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from decimal import Decimal

from mortgageinsurance.models import Monthly, Upfront


class MonthlyTest(APITestCase):
    def populate_db(self):
        """ Prepopulate DB with dummy data. """

        m_ins1_1 = Monthly(insurer='INS1',min_ltv=Decimal("30.001"),max_ltv=Decimal("70"),min_fico=700,max_fico=740,loan_term=30,pmt_type='FIXED',min_loan_amt=Decimal("400000"),max_loan_amt=Decimal("1000000"),premium=Decimal("1.4"))
        m_ins1_1.save()
        m_ins2_1 = Monthly(insurer='INS2',min_ltv=Decimal("30.001"),max_ltv=Decimal("70"),min_fico=700,max_fico=740,loan_term=30,pmt_type='FIXED',min_loan_amt=Decimal("400000"),max_loan_amt=Decimal("1000000"),premium=Decimal("1.6"))
        m_ins2_1.save()
        m_ins1_2 = Monthly(insurer='INS1',min_ltv=Decimal("20.001"),max_ltv=Decimal("30"),min_fico=700,max_fico=740,loan_term=30,pmt_type='FIXED',min_loan_amt=Decimal("400000"),max_loan_amt=Decimal("1000000"),premium=Decimal("0.523"))
        m_ins1_2.save()
        m_ins2_2 = Monthly(insurer='INS2',min_ltv=Decimal("20.001"),max_ltv=Decimal("30"),min_fico=700,max_fico=740,loan_term=30,pmt_type='FIXED',min_loan_amt=Decimal("400000"),max_loan_amt=Decimal("1000000"),premium=Decimal("0.642"))
        m_ins2_2.save()
        m_fha = Monthly(insurer='FHA',min_ltv=Decimal("20.001"),max_ltv=Decimal("70"),min_fico=700,max_fico=740,loan_term=30,pmt_type='FIXED',min_loan_amt=Decimal("400000"),max_loan_amt=Decimal("1000000"),premium=Decimal("0.85"))
        m_fha.save()

        u_fha = Upfront(loan_type='FHA',min_ltv=Decimal("0"), max_ltv=Decimal("80"),premium=Decimal("3.75"))
        u_fha.save()
        u_va_disabled = Upfront(loan_type='VA',va_status='DISABLED',min_ltv=Decimal("0"), max_ltv=Decimal("80"),premium=Decimal("1.5"))
        u_va_disabled.save()
        u_va_regular_y = Upfront(loan_type='VA',va_status='REGULAR',va_first_use='Y',min_ltv=Decimal("0"),max_ltv=Decimal("80"),premium=Decimal("2.0"))
        u_va_regular_y.save()



    def setUp(self):
        self.url = '/oah-api/mortgage-insurance/'
        self.populate_db()

    def test_mortgage_insurance__no_args(self):
        """ ... when no parameters provided """
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('price'), [u'This field is required.'])
        self.assertEqual(response.data.get('loan_amount'), [u'This field is required.'])
        self.assertEqual(response.data.get('minfico'), [u'This field is required.'])
        self.assertEqual(response.data.get('maxfico'), [u'This field is required.'])
        self.assertEqual(response.data.get('loan_term'), [u'This field is required.'])
        self.assertEqual(response.data.get('loan_type'), [u'This field is required.'])
        self.assertEqual(response.data.get('rate_structure'), [u'This field is required.'])
        self.assertEqual(len(response.data), 7)

    # Tests with invalid arguments #

    def test_mortgage_insurance__invalid_no_match(self):
        """ ... when parameters are valid but no matching data in database """

        response_fixed = self.client.get(self.url, 
            {
                'price': 400000,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'conf',
                'rate_structure': 'fixed',
            })
        self.assertEqual(response_fixed.status_code, status.HTTP_200_OK)
        self.assertFalse(response_fixed.data.get('data') is None)
        self.assertTrue(response_fixed.data.get('data').get('monthly')is None)
        self.assertTrue(response_fixed.data.get('data').get('upfront') is None)

    def test_mortgage_insurance__invalid_price(self):
        """ ... when price is 0 """
        response = self.client.get(self.url, 
            {
                'price': 0,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'conf',
                'rate_structure': 'arm',
            })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('price'), [u'price needs to be greater than 0.'])
        self.assertEqual(len(response.data), 1)

    def test_mortgage_insurance__invalid_no_arm_type(self):
        """ ...missing arm_type when rate_structure is arm """
        response = self.client.get(self.url, 
            {
                'price': 700000,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'conf',
                'rate_structure': 'arm',
            })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('non_field_errors'), [u'arm_type is required if rate_structure is ARM'])
        self.assertEqual(len(response.data), 1)

    def test_mortgage_insurance__invalid_arm_type_3_1(self):
        """ ... when arm_type is 3/1 """
        response = self.client.get(self.url, 
            {
                'price': 700000,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'conf',
                'rate_structure': 'arm',
                'arm_type': '3-1',
            })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('non_field_errors'), [u'No mortgage insurance data for 3/1 ARM'])
        self.assertEqual(len(response.data), 1)

    def test_mortgage_insurance__invalid_no_va_status(self):
        """ ... missing va_status when loan_type is va """
        response = self.client.get(self.url, 
            {
                'price': 700000,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'va',
                'rate_structure': 'fixed',
            })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('non_field_errors'), [u'va_status is required if loan_type is VA or VA-HB'])
        self.assertEqual(len(response.data), 1)

    def test_mortgage_insurance__invalid_no_va_first_use(self):
        """ ... missing va_first_use when loan_type is va and va_status is ! disabled """
        response = self.client.get(self.url, 
            {
                'price': 700000,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'va-hb',
                'rate_structure': 'fixed',
                'va_status': 'REGULAR',
            })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('non_field_errors'), [u'va_first_use is required if va_status is not DISABLED'])
        self.assertEqual(len(response.data), 1)


    # Tests with valid arguments #
    def test_mortgage_insurance__valid_fixed_not_VA_FHA(self):
        """ ... when Valid Rate Structure = Fixed, Loan_Type != VA or FHA """

        response_fixed = self.client.get(self.url, 
            {
                'price': 700000,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'conf',
                'rate_structure': 'fixed',
            })
        self.assertEqual(response_fixed.status_code, status.HTTP_200_OK)
        self.assertFalse(response_fixed.data.get('data') is None)
        self.assertEqual(response_fixed.data.get('data').get('monthly'), 1.5)
        self.assertTrue(response_fixed.data.get('data').get('upfront') is None)

    def test_mortgage_insurance__valid_arm_not_VA_FHA(self):
        """ ... when Valid Rate Structure = arm, Loan_Type != VA or FHA """
        response_fixed = self.client.get(self.url, 
            {
                'price': 700000,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'conf',
                'rate_structure': 'arm',
                'arm_type': '7-1'
            })

        self.assertEqual(response_fixed.status_code, status.HTTP_200_OK)
        self.assertFalse(response_fixed.data.get('data') is None)
        self.assertEqual(response_fixed.data.get('data').get('monthly'), 1.5)
        self.assertTrue(response_fixed.data.get('data').get('upfront') is None)

    def test_mortgage_insurance__valid_fixed_FHA(self):
        """ ... when Valid Rate Structure = Fixed, Loan_Type = FHA """
        response_fixed = self.client.get(self.url, 
            {
                'price': 700000,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'fha',
                'rate_structure': 'fixed',
            })
        self.assertEqual(response_fixed.status_code, status.HTTP_200_OK)
        self.assertFalse(response_fixed.data.get('data') is None)
        self.assertEqual(response_fixed.data.get('data').get('monthly'), 0.85)
        self.assertEqual(response_fixed.data.get('data').get('upfront'), 3.75)

    def test_mortgage_insurance__valid_fixed_va_disabled(self):
        """ ... when Valid Rate Structure = Fixed, Loan_Type = VA, VA_Status = DISABLED """
        response_fixed = self.client.get(self.url, 
            {
                'price': 700000,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'va-hb',
                'va_status': 'disabled',
                'rate_structure': 'fixed',
            })
        self.assertEqual(response_fixed.status_code, status.HTTP_200_OK)
        self.assertFalse(response_fixed.data.get('data') is None)
        self.assertTrue(response_fixed.data.get('data').get('monthly') is None)
        self.assertEqual(response_fixed.data.get('data').get('upfront'), 1.5)

    def test_mortgage_insurance__valid_fixed_va_not_disabled(self):
        """ ... when Valid Rate Structure = Fixed, Loan_Type = VA, VA_Status != DISABLED """
        response_fixed = self.client.get(self.url, 
            {
                'price': 700000,
                'loan_amount': 420000,
                'minfico': 700,
                'maxfico': 740,
                'loan_term': 30,
                'loan_type': 'va',
                'va_status': 'regular',
                'va_first_use': 'y',
                'rate_structure': 'fixed',
            })
        self.assertEqual(response_fixed.status_code, status.HTTP_200_OK)
        self.assertFalse(response_fixed.data.get('data') is None)
        self.assertTrue(response_fixed.data.get('data').get('monthly') is None)
        self.assertEqual(response_fixed.data.get('data').get('upfront'), 2.0)

