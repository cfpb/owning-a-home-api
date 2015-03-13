from rest_framework import serializers
from mortgageinsurance.models import MonthlyMortgageIns

# class Params(object):
#     def __init__(self, price, loan_amount, minfico, maxfico, loan_term, va_status):
#         self.price = price
#         self.loan_amount = loan_amount
#         self.minfico = minfico
#         self.maxfico = maxfico
#         self.loan_term = loan_term
#         self.va_status = va_status

class ParamsSerializer(serializers.Serializer):
    #print data
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    minfico = serializers.IntegerField()
    maxfico = serializers.IntegerField()
    loan_term = serializers.DecimalField(max_digits=6, decimal_places=3)
    loan_type = serializers.ChoiceField(choices=MonthlyMortgageIns.LOAN_TYPE_CHOICES)
    rate_structure = serializers.ChoiceField(choices=MonthlyMortgageIns.PAYMENT_TYPE_CHOICES)
    va_status = serializers.CharField(max_length=12, required=False) # Will probably have some choices here

    def validate(self, attrs):
        """
        Check that the start is before the stop.
        """
        # if attrs['start'] > attrs['finish']:
        #     raise serializers.ValidationError("finish must occur after start")
        return attrs

    # check price should be > 0

    # def validate_rate_structure(self, attrs, source):
    #     """
    #     Check that the price is within range
    #     """
    #     value = attrs[source]
    #     print 'attrs: '
    #     print attrs
    #     print 'source'
    #     print source
    #     print 'value'
    #     print value

    #     int(0 if value is None else value)
    #     # if "django" not in value.lower():
    #     #     raise serializers.ValidationError("Blog post is not about Django")
    #     return attrs

    # def validate_va_status(self, attrs, source):
    #     """
    #     Check that the price is within range
    #     """
    #     value = attrs[source]
    #     print 'attrs: '
    #     print attrs
    #     print 'source'
    #     print source
    #     print 'value'
    #     print value

    #     # if "django" not in value.lower():
    #     #     raise serializers.ValidationError("Blog post is not about Django")
    #     return attrs
