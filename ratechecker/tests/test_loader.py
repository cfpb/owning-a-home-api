from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase
from django.utils import timezone

from model_bakery import baker

from ratechecker.loader import (
    AdjustmentLoader,
    Loader,
    LoaderError,
    ProductLoader,
    RateLoader,
    RegionLoader,
    split,
)
from ratechecker.models import Product


class TestSplit(TestCase):
    def test_empty(self):
        chunks = list(split([], chunk_size=1))
        self.assertFalse(chunks)

    def test_single_chunks(self):
        chunks = list(split([1, 2, 3, 4], chunk_size=1))
        self.assertListEqual(chunks, [[1], [2], [3], [4]])

    def test_multiple_chunks(self):
        chunks = list(split([1, 2, 3, 4], chunk_size=2))
        self.assertListEqual(chunks, [[1, 2], [3, 4]])


class UserLoader(Loader):
    model_cls = User

    def make_instance(self, row):
        return self.model_cls(
            username=row["USERNAME"], password=row["PASSWORD"]
        )


class TestLoader(TestCase):
    def test_base_class_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            Loader(ContentFile("HEADER\ncontent")).load()

    def test_empty(self):
        f = ContentFile("HEADER\n")
        with self.assertRaises(LoaderError):
            UserLoader(f).load()
        self.assertFalse(User.objects.exists())

    def test_single_chunk(self):
        f = ContentFile("USERNAME,PASSWORD\n" "username,password")
        UserLoader(f, delimiter=",").load()
        self.assertEqual(User.objects.count(), 1)

    def test_multiple_chunks(self):
        header = "USERNAME,PASSWORD\n"
        f = ContentFile(
            header
            + "\n".join(
                ["username{0},password{0}".format(i) for i in range(10)]
            )
        )
        UserLoader(f, delimiter=",").load()
        self.assertEqual(User.objects.count(), 10)

    def test_nullable_int(self):
        self.assertEqual(Loader.nullable_int("3"), 3)

    def test_nullable_int_strip(self):
        self.assertEqual(Loader.nullable_int(" 3 "), 3)

    def test_nullable_int_float(self):
        self.assertEqual(Loader.nullable_int("3.00"), 3)

    def test_nullable_int_empty(self):
        self.assertIsNone(Loader.nullable_int(""))

    def test_nullable_int_whitespace(self):
        self.assertIsNone(Loader.nullable_int("  "))

    def test_nullable_string(self):
        self.assertEqual(Loader.nullable_string("BANK"), "BANK")

    def test_nullable_string_empty(self):
        self.assertIsNone(Loader.nullable_string(""))

    def test_nullable_string_whitespace(self):
        self.assertIsNone(Loader.nullable_string(" "))

    def test_nullable_decimal(self):
        self.assertEqual(Loader.nullable_decimal("3.5"), Decimal("3.5"))

    def test_nullable_decimal_empty(self):
        self.assertIsNone(Loader.nullable_decimal(""))

    def test_nullable_decimal_whitespace(self):
        self.assertIsNone(Loader.nullable_decimal(" "))

    def test_string_to_boolean_true(self):
        self.assertTrue(Loader.string_to_boolean("true"))

    def test_string_to_boolean_capitalization(self):
        self.assertTrue(Loader.string_to_boolean("TrUe"))

    def test_string_to_boolean_false(self):
        self.assertFalse(Loader.string_to_boolean("false"))

    def test_string_to_boolean_1(self):
        self.assertTrue(Loader.string_to_boolean("1"))

    def test_string_to_boolean_0(self):
        self.assertFalse(Loader.string_to_boolean("0"))

    def test_string_to_boolean_other_is_none(self):
        self.assertIsNone(Loader.string_to_boolean("frog"))

    def test_string_to_boolean_empty(self):
        self.assertIsNone(Loader.string_to_boolean(""))


class LoaderTestCaseMixin(object):
    loader_cls = None

    def load(self, ts=None):
        loader = self.loader_cls(f=None, data_timestamp=ts)
        return loader.make_instance(self.row)

    def test_data_timestamp(self):
        ts = timezone.now()
        self.assertEqual(self.load(ts=ts).data_timestamp, ts)


class TestAdjustmentLoader(LoaderTestCaseMixin, TestCase):
    loader_cls = AdjustmentLoader

    def setUp(self):
        self.row = {
            "planid": "3",
            "ruleid": "2",
            "affectratetype": "foo",
            "adjvalue": "123",
            "minloanamt": "1000",
            "maxloanamt": "10000",
            "proptype": "foo",
            "minfico": "123",
            "maxfico": "456",
            "minltv": "90",
            "maxltv": "100",
            "state": "NY",
        }

    def test_load_product_id(self):
        self.assertEqual(self.load().product_id, 3)

    def test_load_rule_id(self):
        self.assertEqual(self.load().rule_id, 2)

    def test_load_affect_rate_type(self):
        self.assertEqual(self.load().affect_rate_type, "foo")

    def test_load_adj_value(self):
        self.assertEqual(self.load().adj_value, 123)

    def test_load_adj_value_none(self):
        self.row["adjvalue"] = ""
        self.assertEqual(self.load().adj_value, Decimal(0))

    def test_min_loan_amt(self):
        self.assertEqual(self.load().min_loan_amt, Decimal(1000))

    def test_min_loan_amt_none(self):
        self.row["minloanamt"] = ""
        self.assertIsNone(self.load().min_loan_amt)

    def test_max_loan_amt(self):
        self.assertEqual(self.load().max_loan_amt, Decimal(10000))

    def test_max_loan_amt_none(self):
        self.row["maxloanamt"] = ""
        self.assertIsNone(self.load().max_loan_amt)

    def test_prop_type(self):
        self.assertEqual(self.load().prop_type, "foo")

    def test_prop_type_none(self):
        self.row["proptype"] = ""
        self.assertIsNone(self.load().prop_type)

    def test_min_fico(self):
        self.assertEqual(self.load().min_fico, 123)

    def test_min_fico_none(self):
        self.row["minfico"] = ""
        self.assertIsNone(self.load().min_fico)

    def test_max_fico(self):
        self.assertEqual(self.load().max_fico, 456)

    def test_max_fico_none(self):
        self.row["maxfico"] = ""
        self.assertIsNone(self.load().max_fico)

    def test_min_ltv(self):
        self.assertEqual(self.load().min_ltv, Decimal(90))

    def test_min_ltv_none(self):
        self.row["minltv"] = ""
        self.assertIsNone(self.load().min_ltv)

    def test_max_ltv(self):
        self.assertEqual(self.load().max_ltv, Decimal(100))

    def test_max_ltv_none(self):
        self.row["maxltv"] = ""
        self.assertIsNone(self.load().max_ltv)

    def test_state(self):
        self.assertEqual(self.load().state, "NY")


class TestProductLoader(LoaderTestCaseMixin, TestCase):
    loader_cls = ProductLoader

    def setUp(self):
        self.row = {
            "planid": "3",
            "institution": "FOOBAR",
            "loanpurpose": "REFI",
            "pmttype": "FIXED",
            "loantype": "CONF",
            "loanterm": "60",
            "intadjterm": "3",
            "adjperiod": "2",
            "i/o": "0",
            "armindex": "foo",
            "initialadjcap": "12",
            "annualcap": "34",
            "loancap": "56",
            "armmargin": "78",
            "aivalue": "90",
            "minltv": "90",
            "maxltv": "100",
            "minfico": "650",
            "maxfico": "700",
            "minloanamt": "10000",
            "maxloanamt": "100000",
        }

    def test_plan_id(self):
        self.assertEqual(self.load().plan_id, 3)

    def test_institution(self):
        self.assertEqual(self.load().institution, "FOOBAR")

    def test_loan_purpose(self):
        self.assertEqual(self.load().loan_purpose, "REFI")

    def test_pmt_type(self):
        self.assertEqual(self.load().pmt_type, "FIXED")

    def test_loan_type(self):
        self.assertEqual(self.load().loan_type, "CONF")

    def test_loan_term(self):
        self.assertEqual(self.load().loan_term, 60)

    def test_int_adj_term(self):
        self.assertEqual(self.load().int_adj_term, 3)

    def test_int_adj_term_none(self):
        self.row["intadjterm"] = ""
        self.assertIsNone(self.load().int_adj_term)

    def test_adj_period(self):
        self.assertEqual(self.load().adj_period, 2)

    def test_adj_period_none(self):
        self.row["adjperiod"] = ""
        self.assertIsNone(self.load().adj_period)

    def test_io(self):
        self.assertFalse(self.load().io)

    def test_arm_index(self):
        self.assertEqual(self.load().arm_index, "foo")

    def test_arm_index_none(self):
        self.row["armindex"] = ""
        self.assertIsNone(self.load().arm_index)

    def test_int_adj_cap(self):
        self.assertEqual(self.load().int_adj_cap, 12)

    def test_int_adj_cap_none(self):
        self.row["initialadjcap"] = ""
        self.assertIsNone(self.load().int_adj_cap)

    def test_annual_cap(self):
        self.assertEqual(self.load().annual_cap, 34)

    def test_annual_cap_none(self):
        self.row["annualcap"] = ""
        self.assertIsNone(self.load().annual_cap)

    def test_loan_cap(self):
        self.assertEqual(self.load().loan_cap, 56)

    def test_loan_cap_none(self):
        self.row["loancap"] = ""
        self.assertIsNone(self.load().loan_cap)

    def test_arm_margin(self):
        self.assertEqual(self.load().arm_margin, Decimal(78))

    def test_arm_margin_none(self):
        self.row["armmargin"] = ""
        self.assertIsNone(self.load().arm_margin)

    def test_ai_value(self):
        self.assertEqual(self.load().ai_value, Decimal(90))

    def test_ai_value_none(self):
        self.row["aivalue"] = ""
        self.assertIsNone(self.load().ai_value)

    def test_min_ltv(self):
        self.assertEqual(self.load().min_ltv, Decimal(90))

    def test_max_ltv(self):
        self.assertEqual(self.load().max_ltv, Decimal(100))

    def test_min_fico(self):
        self.assertEqual(self.load().min_fico, 650)

    def test_max_fico(self):
        self.assertEqual(self.load().max_fico, 700)

    def test_min_loan_amt(self):
        self.assertEqual(self.load().min_loan_amt, Decimal(10000))

    def test_max_loan_amt(self):
        self.assertEqual(self.load().max_loan_amt, Decimal(100000))


class TestRateLoader(LoaderTestCaseMixin, TestCase):
    loader_cls = RateLoader

    def setUp(self):
        self.product = baker.make(Product, plan_id=3)

        self.row = {
            "ratesid": "123",
            "planid": self.product.plan_id,
            "regionid": "456",
            "lock": "4",
            "baserate": "78",
            "totalpoints": "90",
        }

    def test_rate_id(self):
        self.assertEqual(self.load().rate_id, 123)

    def test_product(self):
        self.assertEqual(self.load().product, self.product)

    def test_region_id(self):
        self.assertEqual(self.load().region_id, 456)

    def test_lock(self):
        self.assertEqual(self.load().lock, 4)

    def test_base_rate(self):
        self.assertEqual(self.load().base_rate, Decimal(78))

    def test_total_points(self):
        self.assertEqual(self.load().total_points, Decimal(90))


class TestRegionLoader(LoaderTestCaseMixin, TestCase):
    loader_cls = RegionLoader

    def setUp(self):
        self.row = {
            "RegionID": "123",
            "StateID": "NY",
        }

    def test_region_id(self):
        self.assertEqual(self.load().region_id, 123)

    def test_state_id(self):
        self.assertEqual(self.load().state_id, "NY")
