from rest_framework import serializers
from mortgageinsurance.models import Monthly, Upfront
from decimal import Decimal

class ParamsSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    minfico = serializers.IntegerField()
    maxfico = serializers.IntegerField()
    loan_term = serializers.IntegerField()
    loan_type = serializers.ChoiceField(choices=Monthly.LOAN_TYPE_CHOICES)
    rate_structure = serializers.ChoiceField(choices=Monthly.PAYMENT_TYPE_CHOICES)
    va_status = serializers.ChoiceField(choices=Upfront.VA_STATUS_CHOICES, required=False) 
    va_first_use = serializers.ChoiceField(choices=Upfront.VA_1ST_USE_CHOICES, required=False)

    def validate(self, attrs):
        """
        Check that va_status is there if loan type is a VA or VA-HB loan.
        """

        if attrs['loan_type'] in (Monthly.VA, Monthly.VA_HB) :

            if not attrs['va_status'] :
                raise serializers.ValidationError("va_status is required if loan_type is VA or VA-HB")

            elif attrs['va_status'] not in (Upfront.DISABLED) and not attrs['va_first_use']:
                raise serializers.ValidationError("va_first_use is required if va_status is not DISABLED")

        return attrs


    def validate_price(self, attrs, source):
        """
        Check that the price is greater than 0
        """
        # This can be avoided if using a newer version (3.0) of Rest Framework, where min_value can be used in DecimalField
        value = attrs[source]
        if attrs[source] <= Decimal('0'):
            raise serializers.ValidationError("This field needs to be greater than 0.")
        return attrs

