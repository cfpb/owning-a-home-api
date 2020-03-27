from decimal import Decimal

from django.test import TestCase

from ratechecker.models import Product
from ratechecker.ratechecker_parameters import ParamsSerializer, scrub_error


class RateCheckerParametersTestCase(TestCase):
    def setUp(self):
        self.data = {
            "price": 240000,
            "loan_amount": 200000,
            "state": "GA",
            "loan_type": "JUMBO",
            "minfico": 700,
            "maxfico": 800,
            "rate_structure": "FIXED",
            "loan_term": 30,
        }

    def test_is_valid__no_args(self):
        serializer = ParamsSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 7)
        self.assertEqual(
            serializer.errors.get("loan_amount"), ["This field is required."]
        )
        self.assertEqual(
            serializer.errors.get("state"), ["This field is required."]
        )
        self.assertEqual(
            serializer.errors.get("loan_type"), ["This field is required."]
        )
        self.assertEqual(
            serializer.errors.get("minfico"), ["This field is required."]
        )
        self.assertEqual(
            serializer.errors.get("maxfico"), ["This field is required."]
        )
        self.assertEqual(
            serializer.errors.get("rate_structure"),
            ["This field is required."],
        )
        self.assertEqual(
            serializer.errors.get("loan_term"), ["This field is required."]
        )

    def test_is_valid__valid_args(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data.get("price"), Decimal("240000")
        )
        self.assertEqual(
            serializer.validated_data.get("loan_amount"), Decimal("200000")
        )
        self.assertEqual(serializer.validated_data.get("state"), "GA")
        self.assertEqual(serializer.validated_data.get("loan_type"), "JUMBO")
        self.assertEqual(serializer.validated_data.get("minfico"), 700)
        self.assertEqual(serializer.validated_data.get("maxfico"), 800)
        self.assertEqual(
            serializer.validated_data.get("rate_structure"), "FIXED"
        )
        self.assertEqual(serializer.validated_data.get("loan_term"), 30)

    def test_is_valid__invalid_lock(self):
        self.data["lock"] = 20
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("lock"), ["lock needs to be 30, 45, or 60."]
        )

    def test_is_valid__lock_default(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data.get("lock"), ParamsSerializer.LOCK
        )
        self.assertEqual(serializer.validated_data.get("min_lock"), 46)
        self.assertEqual(serializer.validated_data.get("max_lock"), 60)

    def test_is_valid__lock_non_default(self):
        self.data["lock"] = 30
        self.data["min_lock"] = 0
        self.data["max_lock"] = 30
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data.get("lock"), 30)
        self.assertEqual(serializer.validated_data.get("min_lock"), 0)
        self.assertEqual(serializer.validated_data.get("max_lock"), 30)

    def test_is_valid__points_default(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data.get("points"), ParamsSerializer.POINTS
        )

    def test_is_valid__points_non_default(self):
        self.data["points"] = 4
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data.get("points"), 4)

    def test_is_valid__property_type_default(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data.get("property_type"),
            ParamsSerializer.PROPERTY_TYPE,
        )

    def test_is_valid__property_type_non_default(self):
        self.data["property_type"] = ParamsSerializer.PROPERTY_TYPE_COOP
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data.get("property_type"),
            ParamsSerializer.PROPERTY_TYPE_COOP,
        )

    def test_is_valid__property_type_invalid(self):
        self.data["property_type"] = "A"
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("property_type"),
            ['"A" is not a valid choice.'],
        )

    def test_is_valid__loan_purpose_default(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data.get("loan_purpose"),
            ParamsSerializer.LOAN_PURPOSE,
        )

    def test_is_valid__loan_purpose_non_default(self):
        self.data["loan_purpose"] = Product.REFI
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data.get("loan_purpose"), Product.REFI
        )

    def test_is_valid__loan_purpose_invalid(self):
        self.data["loan_purpose"] = "A"
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("loan_purpose"),
            ['"A" is not a valid choice.'],
        )

    def test_is_valid__io_default(self):
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data.get("io"), ParamsSerializer.IO
        )

    def test_is_valid__io_non_default(self):
        self.data["io"] = 1
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data.get("io"), 1)

    def test_is_valid__io_invalid(self):
        self.data["io"] = 4
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("io"), ["io needs to be 0 or 1."]
        )

    def test_is_valid__loan_amount_none(self):
        self.data["loan_amount"] = None
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("loan_amount"),
            ["This field may not be null."],
        )

    def test_is_valid__loan_amount_empty(self):
        self.data["loan_amount"] = ""
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("loan_amount"),
            ["A valid number is required."],
        )

    def test_is_valid__loan_amount_negative(self):
        self.data["loan_amount"] = -10000
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data.get("loan_amount"), Decimal("10000")
        )

    def test_is_valid__price(self):
        self.data["price"] = 1000
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["price"], Decimal("1000"))

    def test_is_valid__price_negative(self):
        self.data["price"] = -10000
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data.get("price"), Decimal("10000")
        )

    def test_is_valid__price_zero(self):
        self.data["price"] = 0
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["price"], Decimal("1"))

    def test_is_valid__state_invalid(self):
        self.data["state"] = 123
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("state"), ['"123" is not a valid choice.']
        )

    def test_is_valid__loan_type_invalid(self):
        self.data["loan_type"] = "A"
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("loan_type"), ['"A" is not a valid choice.']
        )

    def test_is_valid__maxfico_smaller(self):
        self.data["maxfico"] = 600
        self.data["minfico"] = 700
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data.get("maxfico"), 700)
        self.assertEqual(serializer.validated_data.get("minfico"), 600)

    def test_is_valid__ficos_negative(self):
        self.data["maxfico"] = -100
        self.data["minfico"] = -200
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data.get("maxfico"), 200)
        self.assertEqual(serializer.validated_data.get("minfico"), 100)

    def test_is_valid__rate_structure_arm_no_arm_type(self):
        self.data["rate_structure"] = "ARM"
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("non_field_errors"),
            ["arm_type is required if rate_structure is ARM."],
        )

    def test_is_valid__loan_term_not_choice(self):
        self.data["loan_term"] = 20
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get("loan_term"),
            ["loan_term needs to be 15 or 30."],
        )

    def test_is_valid__loan_term_negative(self):
        self.data["loan_term"] = -30
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data.get("loan_term"), 30)

    def test_is_valid__ltv__without_ltv(self):
        self.data["price"] = 200000
        self.data["loan_amount"] = 180000
        serializer = ParamsSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data.get("min_ltv"), 90)
        self.assertTrue(
            serializer.validated_data.get("min_ltv"),
            serializer.validated_data.get("max_ltv"),
        )

    def test_is_valid__ltv__without_price(self):
        data = dict(self.data)
        data["ltv"] = 90
        data.pop("price", None)
        serializer = ParamsSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_is_valid_only_price_or_ltv_not_both(self):
        self.data["price"] = 200000
        self.data["loan_amount"] = 180000
        self.data["ltv"] = 90.100
        serializer = ParamsSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())

    def test_is_valid_no_price_or_ltv(self):
        data = dict(self.data)
        data.pop("price", None)
        data.pop("ltv", None)
        serializer = ParamsSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "one of price or ltv is required",
            serializer.errors["non_field_errors"],
        )

    def test_error_scrubber(self):
        bad_value1 = "CONFFQ684<SCRIPT>ALERT(1)</SCRIPT>"
        bad_value2 = r"%3Cscript%3CEalert(1)%3C%2fscript%3E"
        for char in ["<", ">", r"%3C", r"%3E"]:
            self.assertNotIn(char, scrub_error(bad_value1))
            self.assertNotIn(char, scrub_error(bad_value2))

    def test_error_scrubber_called_without_is_valid_raises_error(self):
        serializer = ParamsSerializer(data=self.data)
        with self.assertRaises(AssertionError):
            serializer.errors
