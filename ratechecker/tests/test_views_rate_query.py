from django.test import TestCase
from django.utils import timezone

from ratechecker.models import Adjustment, Product, Rate, Region
from ratechecker.views import get_rates


class Object(object):
    pass


class RateQueryTestCase(TestCase):
    def setUp(self):
        REGIONS = [[1, "DC"], [2, "VA"], [3, "MD"]]
        PRODUCTS = [
            # plan_id, institution, loan_purpose, pmt_type, loan_type, loan_term, int_adj_term, _, io, _, _, _, _, _, _,  # noqa
            # min_ltv, max_ltv, minfico, maxfico, min_loan_amt, max_loan_amt, single_family, condo, coop  # noqa
            [
                11,
                "Institution 1",
                "PURCH",
                "FIXED",
                "CONF",
                30,
                None,
                None,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                95,
                680,
                700,
                90000,
                750000,
                1,
                0,
                0,
            ],
            [
                22,
                "Institution 2",
                "PURCH",
                "FIXED",
                "CONF",
                30,
                None,
                None,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                87,
                680,
                740,
                90000,
                550000,
                1,
                0,
                0,
            ],
            [
                33,
                "Institution 3",
                "PURCH",
                "ARM",
                "CONF",
                15,
                5,
                None,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                95,
                680,
                740,
                90000,
                550000,
                1,
                0,
                0,
            ],
            [
                44,
                "Institution 4",
                "PURCH",
                "FIXED",
                "CONF",
                30,
                None,
                None,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                87,
                680,
                740,
                90000,
                550000,
                1,
                0,
                0,
            ],
            [
                55,
                "Institution 5",
                "PURCH",
                "ARM",
                "CONF",
                30,
                5,
                None,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                87,
                680,
                740,
                90000,
                550000,
                1,
                0,
                0,
            ],
            [
                66,
                "Institution 6",
                "PURCH",
                "FIXED",
                "CONF",
                30,
                None,
                None,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                87,
                680,
                740,
                90000,
                550000,
                1,
                0,
                0,
            ],
            [
                77,
                "Institution 7",
                "PURCH",
                "FIXED",
                "FHA-HB",
                15,
                None,
                None,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                87,
                680,
                740,
                90000,
                550000,
                1,
                0,
                0,
            ],
            [
                88,
                "Institution 8",
                "PURCH",
                "FIXED",
                "FHA",
                30,
                None,
                None,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                87,
                680,
                740,
                90000,
                550000,
                1,
                0,
                0,
            ],
            [
                98,
                "Institution 8",
                "PURCH",
                "FIXED",
                "CONF",
                30,
                None,
                None,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                95,
                680,
                740,
                90000,
                550000,
                1,
                1,
                0,
            ],
            [
                99,
                "Institution 8",
                "PURCH",
                "FIXED",
                "CONF",
                30,
                None,
                None,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                90,
                680,
                740,
                90000,
                550000,
                1,
                1,
                0,
            ],
        ]
        RATES = [
            # rate_id, product_id, region_id, lock, base_rate, total_points
            [111, 11, 1, 50, "3.150", "0.5"],
            [112, 11, 2, 60, "4.350", "-0.5"],
            [113, 11, 1, 60, "2.125", "0.125"],
            [221, 22, 1, 60, "3.555", "0.125"],
            [331, 33, 1, 60, "3.250", "0.125"],
            [332, 33, 2, 60, "4.650", "-0.5"],
            [441, 44, 1, 50, "3.125", "1.25"],
            [551, 55, 1, 50, "0.125", "0.125"],
            [661, 66, 1, 60, "3.705", "0.5"],
            [771, 77, 2, 60, "1.705", "0.25"],
            [772, 77, 2, 60, "2.705", "1.25"],
            [881, 88, 1, 60, "3.000", "0.5"],
            [882, 88, 1, 60, "2.005", "0.25"],
            [883, 88, 1, 60, "1.005", "-0.25"],
            [884, 98, 3, 60, "3.000", "0.5"],
            [885, 98, 3, 60, "2.985", "0"],
            [886, 98, 3, 60, "1.985", "-0.25"],
            [887, 99, 3, 60, "3.000", "0.5"],
            [888, 99, 3, 60, "2.995", "0"],
            [889, 99, 3, 60, "1.995", "-0.25"],
        ]
        ADJUSTMENTS = [
            # rule_id, product_id, affect_rate_type, adj_value, min_loan_amt,
            # max_loan_amt, prop_type, minfico, maxfico, minltv, maxltv, state
            [
                1,
                11,
                "P",
                "-0.35",
                100000,
                500000,
                "CONDO",
                660,
                780,
                30,
                95,
                "DC",
            ],
            [
                2,
                11,
                "P",
                "0.25",
                100000,
                500000,
                "CONDO",
                660,
                780,
                30,
                95,
                "DC",
            ],
            [
                3,
                11,
                "R",
                "0.15",
                100000,
                500000,
                "CONDO",
                660,
                780,
                30,
                95,
                "DC",
            ],
            [
                4,
                22,
                "R",
                "0.25",
                100000,
                500000,
                "CONDO",
                660,
                780,
                30,
                95,
                "VA",
            ],
            [
                5,
                22,
                "R",
                "0.15",
                100000,
                500000,
                "CONDO",
                660,
                780,
                30,
                95,
                "DC",
            ],
            [
                6,
                33,
                "R",
                "0.25",
                100000,
                500000,
                "CONDO",
                660,
                780,
                30,
                95,
                "DC",
            ],
            [
                7,
                77,
                "P",
                "0.125",
                100000,
                500000,
                "CONDO",
                660,
                780,
                30,
                95,
                "VA",
            ],
            [
                8,
                98,
                "P",
                "0.125",
                100000,
                500000,
                "CONDO",
                660,
                780,
                30,
                95,
                "MD",
            ],
            [
                9,
                99,
                "P",
                "0.125",
                100000,
                500000,
                "CONDO",
                660,
                780,
                30,
                95,
                "MD",
            ],
        ]
        self.NOW = timezone.now()
        NOW = self.NOW

        for region in REGIONS:
            reg = Region(
                region_id=region[0], state_id=region[1], data_timestamp=NOW
            )
            reg.save()

        for p in PRODUCTS:
            product = Product(
                plan_id=p[0],
                institution=p[1],
                loan_purpose=p[2],
                pmt_type=p[3],
                loan_type=p[4],
                loan_term=p[5],
                int_adj_term=p[6],
                adj_period=p[7],
                io=p[8],
                arm_index=p[9],
                int_adj_cap=p[10],
                annual_cap=p[11],
                loan_cap=p[12],
                arm_margin=p[13],
                ai_value=p[14],
                min_ltv=p[15],
                max_ltv=p[16],
                min_fico=p[17],
                max_fico=p[18],
                min_loan_amt=p[19],
                max_loan_amt=p[20],
                single_family=p[21],
                condo=p[22],
                coop=p[23],
                data_timestamp=NOW,
            )
            product.save()

        for r in RATES:
            rate = Rate(
                rate_id=r[0],
                product_id=r[1],
                region_id=r[2],
                lock=r[3],
                base_rate=r[4],
                total_points=r[5],
                data_timestamp=NOW,
            )
            rate.save()

        for a in ADJUSTMENTS:
            adjustment = Adjustment(
                rule_id=a[0],
                product_id=a[1],
                affect_rate_type=a[2],
                adj_value=a[3],
                min_loan_amt=a[4],
                max_loan_amt=a[5],
                prop_type=a[6],
                min_fico=a[7],
                max_fico=a[8],
                min_ltv=a[9],
                max_ltv=a[10],
                state=a[11],
                data_timestamp=NOW,
            )
            adjustment.save()

    def initialize_params(self, values=None):
        """a helper method to init params"""
        if values is None:
            values = {}
        self.params = Object
        self.params.state = values.get("state", "DC")
        self.params.loan_purpose = values.get("loan_purpose", "PURCH")
        self.params.rate_structure = values.get("rate_structure", "FIXED")
        self.params.loan_type = values.get("loan_type", "CONF")
        self.params.max_ltv = values.get("max_ltv", 50)
        self.params.min_ltv = values.get("min_ltv", 50)
        self.params.loan_term = values.get("loan_term", 30)
        self.params.loan_amount = values.get("loan_amount", 160000)
        self.params.price = values.get("price", 320000)
        self.params.maxfico = values.get("maxfico", 700)
        self.params.minfico = values.get("minfico", 700)
        self.params.lock = values.get("lock", 60)
        self.params.max_lock = values.get("max_lock", 60)
        self.params.min_lock = values.get("min_lock", 45)
        self.params.property_type = values.get("property_type", "CONDO")
        self.params.points = values.get("points", 0)
        self.params.arm_type = values.get("arm_type", "5-1")
        self.params.io = 0

    def test_get_rates__no_results(self):
        """... get_rates with a valid state for which there's no data."""
        self.initialize_params({"state": "IL"})
        result = get_rates(self.params.__dict__, return_fees=True)
        self.assertFalse(result["data"])
        self.assertFalse(result["timestamp"])
        self.assertFalse("fees" in result)

    def test_get_rates__rate_structure(self):
        """... get_rates, different values for rate_structure param."""
        self.initialize_params()
        result = get_rates(self.params.__dict__)
        self.assertTrue(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result["data"]), 2)
        self.assertEqual(result["data"]["2.275"], 1)
        self.assertEqual(result["data"]["3.705"], 2)

        self.initialize_params({"rate_structure": "ARM"})
        result = get_rates(self.params.__dict__)
        self.assertTrue(result)
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"]["0.125"], 1)

        self.initialize_params({"rate_structure": "ARM", "loan_term": 15})
        result = get_rates(self.params.__dict__)
        self.assertTrue(result)
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"]["3.500"], 1)

        # loan_amount is less than min_loan_amt
        self.initialize_params(
            {"rate_structure": "ARM", "loan_term": 15, "loan_amount": 10000}
        )
        result = get_rates(self.params.__dict__)
        self.assertFalse(result["data"])
        self.assertTrue(result["timestamp"])

    def test_get_rates__loan_type(self):
        """diff values for loan_type param."""
        # actually only HighBalance ones
        self.initialize_params(
            {
                "loan_type": "FHA-HB",
                "loan_term": 15,
                "loan_amount": 10000,
                "state": "VA",
            }
        )
        result = get_rates(self.params.__dict__)
        self.assertTrue(result)
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"]["1.705"], 1)

    def test_get_rates__plan_selection_logic(self):
        """... see that the correct selection is done
        when several row of same product_id are present."""
        self.initialize_params({"loan_type": "FHA"})
        result = get_rates(self.params.__dict__)
        self.assertTrue(result)
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"]["2.005"], 1)

    def test_get_rates__data_load_testing(self):
        """... check that factor = -1 is applied to the results."""
        self.initialize_params()
        self.params.state = "MD"
        self.params.institution = "Institution 8"
        result = get_rates(self.params.__dict__, data_load_testing=True)
        self.assertTrue(result)
        self.assertEqual(len(result["data"]), 2)
        self.assertEqual(result["data"]["1.995"], "-0.125")
        self.assertEqual(result["data"]["1.985"], "-0.125")
        result = get_rates(self.params.__dict__, data_load_testing=False)
        self.assertTrue(result)
        self.assertEqual(len(result["data"]), 2)
        self.assertEqual(result["data"]["2.995"], 1)
        self.assertEqual(result["data"]["2.985"], 1)
