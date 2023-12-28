from decimal import Decimal

from localflavor.us.us_states import STATE_CHOICES
from rest_framework import serializers

from ratechecker.models import Product


def scrub_error(error):
    for char in ["<", ">", r"%3C", r"%3E"]:
        error = error.replace(char, "")
    return error


class ParamsSerializer(serializers.Serializer):
    PROPERTY_TYPE_SF = "SF"
    PROPERTY_TYPE_COOP = "COOP"
    PROPERTY_TYPE_CONDO = "CONDO"

    PROPERTY_TYPE_CHOICES = (
        (PROPERTY_TYPE_SF, "Single Family"),
        (PROPERTY_TYPE_COOP, "Co-operative"),
        (PROPERTY_TYPE_CONDO, "Condominum"),
    )

    ARM_TYPE_3_1 = "3-1"
    ARM_TYPE_5_1 = "5-1"
    ARM_TYPE_7_1 = "7-1"
    ARM_TYPE_10_1 = "10-1"

    ARM_TYPE_CHOICES = (
        (ARM_TYPE_3_1, "3/1 ARM"),
        (ARM_TYPE_5_1, "5/1 ARM"),
        (ARM_TYPE_7_1, "7/1 ARM"),
        (ARM_TYPE_10_1, "10/1 ARM"),
    )

    # Default
    LOCK = 60
    LOCK_MIN = 46
    LOCK_MAX = 60
    POINTS = 0
    IO = 0
    PROPERTY_TYPE = PROPERTY_TYPE_SF
    LOAN_PURPOSE = Product.PURCH

    lock = serializers.IntegerField(default=LOCK)
    min_lock = serializers.IntegerField(default=LOCK_MIN)
    max_lock = serializers.IntegerField(default=LOCK_MAX)
    points = serializers.IntegerField(default=POINTS)
    property_type = serializers.ChoiceField(
        choices=PROPERTY_TYPE_CHOICES, default=PROPERTY_TYPE
    )
    loan_purpose = serializers.ChoiceField(
        choices=Product.LOAN_PURPOSE_CHOICES, default=LOAN_PURPOSE
    )
    io = serializers.IntegerField(default=IO)
    institution = serializers.CharField(max_length=20, required=False)
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False
    )
    state = serializers.ChoiceField(choices=STATE_CHOICES)
    loan_type = serializers.ChoiceField(choices=Product.LOAN_TYPE_CHOICES)
    minfico = serializers.IntegerField()
    maxfico = serializers.IntegerField()
    rate_structure = serializers.ChoiceField(
        choices=Product.PAYMENT_TYPE_CHOICES
    )
    arm_type = serializers.ChoiceField(
        choices=ARM_TYPE_CHOICES, required=False
    )
    loan_term = serializers.IntegerField()
    ltv = serializers.DecimalField(
        max_digits=6, decimal_places=3, required=False
    )
    min_ltv = serializers.DecimalField(
        max_digits=6, decimal_places=3, required=False
    )
    max_ltv = serializers.DecimalField(
        max_digits=6, decimal_places=3, required=False
    )

    def validate(self, attrs):
        """
        Validate parameters that are required due to the value of other params.
        """
        if attrs["rate_structure"] == Product.ARM:
            if not attrs.get("arm_type"):
                raise serializers.ValidationError(
                    "arm_type is required if rate_structure is ARM."
                )

        price = attrs.get("price")
        ltv = attrs.get("ltv")

        if (not price and not ltv) or (price and ltv):
            raise serializers.ValidationError(
                "one of price or ltv is required"
            )

        loan_amount = attrs["loan_amount"]

        if price and not ltv:
            attrs["ltv"] = Decimal(loan_amount) / price * 100
        if ltv and not price:
            attrs["price"] = Decimal(loan_amount) / ltv * 100

        attrs["min_ltv"] = attrs["max_ltv"] = attrs["ltv"]

        # Fix the min/max ltv
        attrs["minfico"] = abs(attrs["minfico"])
        attrs["maxfico"] = abs(attrs["maxfico"])

        if attrs["minfico"] > attrs["maxfico"]:
            attrs["minfico"], attrs["maxfico"] = (
                attrs["maxfico"],
                attrs["minfico"],
            )

        return attrs

    def validate_price(self, value):
        """
        Validate price, convert to positive if negative, and enforce a
        minimum value of 0.
        """
        if value and value < 0:
            value = abs(value)
        elif value == 0:
            value = Decimal("1")

        return value

    def validate_lock(self, value):
        """
        Check that the lock is 30, 45, or 60
        """
        # @TODO maybe there's a better way to do this with integer choice?
        if value not in (30, 45, 60):
            raise serializers.ValidationError(
                "lock needs to be " "30, 45, or 60."
            )
        return value

    def validate_io(self, value):
        """
        Check that the io is 0 or 1
        """
        if value not in (0, 1):
            raise serializers.ValidationError("io needs to be 0 or 1.")
        return value

    def validate_loan_amount(self, value):
        """
        Change loan amount to positive if negative
        """
        if value < 0:
            value = abs(value)
        return value

    def validate_loan_term(self, value):
        """
        Check that loan term is 15 or 30
        """
        # @TODO maybe there's a better way to do this with integer choice?
        if value < 0:
            value = abs(value)

        if value not in (15, 30):
            raise serializers.ValidationError(
                "loan_term needs to be " "15 or 30."
            )
        return value

    @property
    def errors(self):
        if not hasattr(self, "_errors"):
            msg = "You must call `.is_valid()` before accessing `.errors`."
            raise AssertionError(msg)
        for key in self._errors.keys():
            self._errors[key] = [
                scrub_error(error) for error in self._errors[key]
            ]  # noqa

        return self._errors
