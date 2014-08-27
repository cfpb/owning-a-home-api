from django.shortcuts import render
from django.db.models import Q, Sum

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ratechecker.models import Product, Region, Rate, Adjustment


class RateCheckerParameters(object):
    """ The rate checker API has a long list of
    parameters that need to be validated. This class helps with
    that. """

    def __init__(self):
        self.LOAN_TYPES = [c[0] for c in Product.LOAN_TYPE_CHOICES]
        self.PAYMENT_TYPES = [c[0] for c in Product.PAYMENT_TYPE_CHOICES]

        #Here are parameters that are currently not changeable.
        self.lock = 60
        self.points = 0
        self.property_type = 'SF'
        self.loan_purpose = Product.PURCH

        self.calculate_locks()

    def calculate_locks(self):
        locks = {
            30: (0, 30),
            45: (31, 45),
            60: (46, 60)}
        self.min_lock, self.max_lock = locks[self.lock]

    def set_loan_amount(self, amount):
        self.loan_amount = int(amount)

    def set_price(self, price):
        self.price = int(price)

    def set_state(self, state_two_letter):
        self.state = state_two_letter

    def set_loan_type(self, loan_type):
        if loan_type.upper() in self.LOAN_TYPES:
            self.loan_type = loan_type.upper()
        else:
            raise ValueError('loan_type is not one of acceptable value.')

    def set_ficos(self, minfico, maxfico):
        minfico = int(minfico)
        maxfico = int(maxfico)

        if minfico > maxfico:
            minfico, maxfico = maxfico, minfico

        # So that results don't overlap. (This behavior is from the
        # older version of the API.
        if minfico != maxfico:
            maxfico -= 1

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
                raise ValueError('You must provide a valid arm_type.')

    def set_loan_term(self, loan_term):
        self.loan_term = int(loan_term)

    def calculate_loan_to_value(self):
        """
            Calculate and save the loan to value ratio (LTV). We store this
            as min and max LTV values for historical reasons.
        """

        self.min_ltv = self.loan_amount / float(self.price) * 100.0
        self.max_ltv = self.min_ltv

    def set_from_query_params(self, query):
        """ Populate params from query string."""
        try:
            loan_amount = query['loan_amount']
            price = query['price']
            state = query['state']
            loan_type = query['loan_type']
            maxfico = query['maxfico']
            minfico = query['minfico']
            loan_term = query['loan_term']
            rate_structure = query['rate_structure']
            arm_type = query.get('arm_type', None)
        except KeyError as e:
            msg = "Required parameter %s is missing" % str(e.args[0])
            raise KeyError(msg)

        self.set_loan_amount(loan_amount)
        self.set_price(price)
        self.set_state(state)
        self.set_loan_type(loan_type)
        self.set_ficos(minfico, maxfico)
        self.set_rate_structure(rate_structure, arm_type)
        self.set_loan_term(loan_term)
        self.calculate_loan_to_value()


def rate_query(params):
    """ params is a method parameter of type RateCheckerParameters. """
    region_ids = Region.objects.filter(
        state_id=params.state).values_list('region_id', flat=True)

    rates = Rate.objects.filter(
        region_id__in=region_ids,
        product__loan_purpose=params.loan_purpose,
        product__pmt_type=params.rate_structure,
        product__loan_type=params.loan_type,
        product__max_ltv__gte=params.max_ltv,
        product__max_loan_amt__gte=params.loan_amount,
        product__loan_term=params.loan_term,
        lock__lte=params.max_lock,
        lock__gt=params.min_lock)

    deduped_rates = rates.values_list('product__plan_id', 'region_id').distinct()
    product_ids = [p[0] for p in deduped_rates]

    adjustments = Adjustment.objects.filter(product__plan_id__in=product_ids).filter(
        Q(min_loan_amt__lte=params.loan_amount) | Q(min_loan_amt__isnull=True),
        Q(max_loan_amt__gte=params.loan_amount) | Q(max_loan_amt__isnull=True),
        Q(prop_type=params.property_type) | Q(prop_type__isnull=True),
        Q(state=params.state) | Q(state__isnull=True) | Q(state=""),
        Q(max_fico__gte=params.maxfico) | Q(max_fico__isnull=True),
        Q(min_fico__lte=params.minfico) | Q(min_fico__isnull=True),
        Q(min_ltv__lte=params.min_ltv) | Q(min_ltv__isnull=True),
        Q(max_ltv__gte=params.max_ltv) | Q(max_ltv__isnull=True),
    ).values('product_id').annotate(sum_of_adjvalue=Sum('adj_value'))

    summed_adj_dict = dict(adjustments.values_list('product_id', 'sum_of_adjvalue'))
    available_rates = {}
    for rate in rates:
        rate.total_points += summed_adj_dict.get(rate.product_id, 0)
        if abs(params.points - rate.total_points) > 0.5:
            continue
        if rate.product_id not in available_rates:
            available_rates[rate.product_id] = rate
        else:
            current_difference = abs(params.points - available_rates[rate.product_id].total_points)
            new_difference = abs(params.points - rate.total_points)
            if new_difference < current_difference or (
                    new_difference == current_difference and
                    available_rates[rate.product_id].total_points < 0 and
                    rate.total_points > 0):
                available_rates[rate.product_id] = rate
    data = {}
    for rate in available_rates:
        key = str(available_rates[rate].base_rate)
        current_value = data.get(key, 0)
        data[key] = current_value + 1

    return data


@api_view(['GET'])
def rate_checker(request):
    """ This is a just a simple API for example purposes. Let's replace this
    with a real one as soon as we can. """

    if request.method == 'GET':

        parameters = RateCheckerParameters()
        try:
            parameters.set_from_query_params(request.QUERY_PARAMS)
            rate_results = rate_query(parameters)
        except KeyError as e:
            error_response = {'detail': str(e.args[0])}
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        return Response({'results': rate_results})
