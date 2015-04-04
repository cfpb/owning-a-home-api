from rest_framework import serializers
import re
from decimal import Decimal

from ratechecker.models import Product
from localflavor.us.us_states import STATE_CHOICES

class ParamsSerializer(serializers.Serializer):
    LOCK_30 = 30
    LOCK_45 = 45
    LOCK_60 = 60

    LOCK_CHOICES = (
        (LOCK_30, LOCK_30),
        (LOCK_45, LOCK_45),
        (LOCK_60, LOCK_60),
    )

    PROPERTY_TYPE_SF = 'SF'
    PROPERTY_TYPE_COOP = 'COOP'
    PROPERTY_TYPE_CONDO = 'CONDO'

    PROPERTY_TYPE_CHOICES = (
        (PROPERTY_TYPE_SF, 'Single Family'),
        (PROPERTY_TYPE_COOP, 'Co-operative'),
        (PROPERTY_TYPE_CONDO, 'Condominum'),
    )

    IO_TRUE = 1
    IO_FALSE = 0

    IO_CHOICES = (
        (IO_TRUE, IO_TRUE),
        (IO_FALSE, IO_FALSE),
    )

    ARM_TYPE_3_1 = '3-1'
    ARM_TYPE_5_1 = '5-1'
    ARM_TYPE_7_1 = '7-1'
    ARM_TYPE_10_1 = '10-1'

    ARM_TYPE_CHOICES = (
        (ARM_TYPE_3_1, '3/1 ARM'),
        (ARM_TYPE_5_1, '5/1 ARM'),
        (ARM_TYPE_7_1, '7/1 ARM'),
        (ARM_TYPE_10_1, '10/1 ARM'),
    )

    def __init__(self, instance=None, data={}, **kwargs):

        fixed_data = {}

        # @TODO: There must be a better way to do this
        if data:
            if data.get('lock'):
                fixed_data['lock'] = data.get('lock')
            if data.get('points'):
                fixed_data['points'] = data.get('points')
            if data.get('property_type'):
                fixed_data['property_type'] = data.get('property_type').strip().upper()
            if data.get('loan_purpose'):
                fixed_data['loan_purpose'] = data.get('loan_purpose').strip().upper()
            if data.get('io'):
                fixed_data['io'] = data.get('io')
            if data.get('institution'):
                fixed_data['institution'] = data.get('institution').strip().upper()
            if data.get('loan_amount'):
                fixed_data['loan_amount'] = data.get('loan_amount')
            if data.get('price'):
                fixed_data['price'] = data.get('price')
            if data.get('state'):
                fixed_data['state'] = data.get('state').strip().upper()
            if data.get('loan_type'):
                fixed_data['loan_type'] = data.get('loan_type').strip().upper()
            if data.get('maxfico'):
                fixed_data['maxfico'] = data.get('maxfico')
            if data.get('minfico'):
                fixed_data['minfico'] = data.get('minfico')
            if data.get('loan_term'):
                fixed_data['loan_term'] = data.get('loan_term')
            if data.get('rate_structure'):
                fixed_data['rate_structure'] = data.get('rate_structure').strip().upper()
            if data.get('arm_type'):
                fixed_data['arm_type'] = data.get('arm_type').strip().upper()
            if data.get('ltv'):
                fixed_data = data.get('ltv')


        super(ParamsSerializer, self).__init__(data=fixed_data, **kwargs)
    

    lock = serializers.IntegerField(default=60, required=False)
    min_lock = serializers.IntegerField(required=False)
    max_lock = serializers.IntegerField(required=False)
    points = serializers.IntegerField(default=0, required=False)
    property_type = serializers.ChoiceField(choices=PROPERTY_TYPE_CHOICES, default=PROPERTY_TYPE_SF, required=False)
    loan_purpose = serializers.ChoiceField(choices=Product.LOAN_PURPOSE_CHOICES, default=Product.PURCH, required=False)
    io = serializers.IntegerField(default=IO_FALSE, required=False)
    institution = serializers.CharField(max_length=20, required=False)
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    state = serializers.ChoiceField(choices=STATE_CHOICES)
    loan_type = serializers.ChoiceField(choices=Product.LOAN_TYPE_CHOICES)
    minfico = serializers.IntegerField()
    maxfico = serializers.IntegerField()
    rate_structure = serializers.ChoiceField(choices=Product.PAYMENT_TYPE_CHOICES)
    arm_type = serializers.ChoiceField(choices=ARM_TYPE_CHOICES, required=False)
    loan_term = serializers.IntegerField()
    ltv = serializers.DecimalField(max_digits=6, decimal_places=3, required=False)
    min_ltv = serializers.DecimalField(max_digits=6, decimal_places=3, required=False)
    max_ltv = serializers.DecimalField(max_digits=6, decimal_places=3, required=False)

    # def validate_state(self, attrs, source):
    #     attrs[source] = attrs[source].strip().upper()
    #     if attrs[source] not in STATE_CHOICES:
    #         raise serializers.ValidationError("Select a valid choice.")
    #     return attrs


    def calculate_locks(self):
        locks = {
            30: (0, 30),
            45: (31, 45),
            60: (46, 60)}
        self.data['min_lock'], self.data['max_lock'] = locks.get(self.data.get('lock'))

    def calculate_loan_to_value(self):
        """
            Calculate and save the loan to value ratio (LTV). We store this
            as min and max LTV values for historical reasons.
        """

        # if ltv:
        #     ltv = Decimal("%f" % ltv).quantize(Decimal('.001'))

        self.data['min_ltv'] = Decimal("%f" % (self.data['loan_amount'] / self.data['price'] * 100)).quantize(Decimal('.001'))
        self.data['max_ltv'] = self.data['min_ltv']

        # if ltv and abs(ltv - self.max_ltv) < 1:
        #     self.max_ltv = self.min_ltv = ltv


    def calculate_data(self):
        self.calculate_locks()
        self.calculate_loan_to_value()

class RateCheckerParameters(object):
    """ The rate checker API has a long list of
    parameters that need to be validated. This class helps with
    that. """

    # defaults
    LOCK = 60
    POINTS = 0
    PROPERTY_TYPE = 'SF'
    LOAN_PURPOSE = Product.PURCH
    IO = 0

    def __init__(self):
        self.LOAN_TYPES = [c[0] for c in Product.LOAN_TYPE_CHOICES]
        self.PAYMENT_TYPES = [c[0] for c in Product.PAYMENT_TYPE_CHOICES]

    def set_lock(self, lock):
        if lock:
            self.lock = lock
        else:
            self.lock = self.LOCK
        self.calculate_locks(self.lock)

    def set_points(self, points):
        if points:
            self.points = points
        else:
            self.points = self.POINTS

    def set_property_type(self, property_type):
        if property_type:
            self.property_type = property_type
        else:
            self.property_type = self.PROPERTY_TYPE

    def set_loan_purpose(self, loan_purpose):
        if loan_purpose:
            self.loan_purpose = loan_purpose
        else:
            self.loan_purpose = self.LOAN_PURPOSE

    def set_io(self, io):
        if io:
            self.io = io
        else:
            self.io = self.IO

    def set_institution(self, institution):
        self.institution = institution

    def calculate_locks(self, lock):
        locks = {
            30: (0, 30),
            45: (31, 45),
            60: (46, 60)}
        self.min_lock, self.max_lock = locks[lock]

    def set_loan_amount(self, amount):
        self.loan_amount = abs(int(amount))

    def set_price(self, price):
        self.price = abs(int(price))

    def set_state(self, state_two_letter):
        self.state = state_two_letter

    def set_loan_type(self, loan_type):
        if loan_type.upper() in self.LOAN_TYPES:
            self.loan_type = loan_type.upper()
        else:
            raise ValueError('loan_type is not one of acceptable value.')

    def set_ficos(self, minfico, maxfico):
        minfico = abs(int(minfico))
        maxfico = abs(int(maxfico))

        if minfico > maxfico:
            minfico, maxfico = maxfico, minfico

        self.minfico = minfico
        self.maxfico = maxfico

    def set_rate_structure(self, rate_structure, arm_type):
        rate_structure = rate_structure.upper()

        if rate_structure in self.PAYMENT_TYPES:
            self.rate_structure = rate_structure
        else:
            raise ValueError('rate_structure is not one of acceptable values')

        if rate_structure == Product.ARM:
            if arm_type is not None and arm_type in Product.ARM_TYPES:
                self.arm_type = arm_type
            else:
                raise ValueError('You must provide a valid arm_type. %s' % arm_type)

    def set_loan_term(self, loan_term):
        self.loan_term = abs(int(loan_term))

    def calculate_loan_to_value(self, ltv=None):
        """
            Calculate and save the loan to value ratio (LTV). We store this
            as min and max LTV values for historical reasons.
        """

        if ltv:
            ltv = Decimal("%f" % ltv).quantize(Decimal('.001'))

        self.min_ltv = Decimal("%f" % (1.0 * self.loan_amount / self.price * 100)).quantize(Decimal('.001'))
        self.max_ltv = self.min_ltv

        if ltv and abs(ltv - self.max_ltv) < 1:
            self.max_ltv = self.min_ltv = ltv

    def set_from_query_params(self, query):
        """ Populate params from query string."""
        try:
            lock = query.get('lock', None)
            points = query.get('points', None)
            property_type = query.get('property_type', None)
            loan_purpose = query.get('loan_purpose', None)
            io = query.get('io', None)
            institution = query.get('institution', '')
            loan_amount = query['loan_amount']
            price = query['price']
            state = query['state']
            loan_type = query['loan_type']
            maxfico = query['maxfico']
            minfico = query['minfico']
            loan_term = query['loan_term']
            rate_structure = query['rate_structure']
            arm_type = query.get('arm_type', None)
            ltv = query.get('ltv', None)
        except KeyError as e:
            param_name = re.sub(r'"Key (\'\w+\').+', r'\g<1>', str(e))
            msg = "Required parameter %s is missing" % param_name
            raise KeyError(msg)

        self.set_lock(lock)
        self.calculate_locks(self.lock)
        self.set_points(points)
        self.set_property_type(property_type)
        self.set_loan_purpose(loan_purpose)
        self.set_io(io)
        self.set_institution(institution)
        self.set_loan_amount(loan_amount)
        self.set_price(price)
        self.set_state(state)
        self.set_loan_type(loan_type)
        self.set_ficos(minfico, maxfico)
        self.set_rate_structure(rate_structure, arm_type)
        self.set_loan_term(loan_term)
        self.calculate_loan_to_value(ltv)