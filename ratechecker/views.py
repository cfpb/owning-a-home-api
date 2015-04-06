from django.shortcuts import render
from django.db.models import Q, Sum

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ratechecker.models import Product, Region, Rate, Adjustment
from ratechecker.ratechecker_parameters import RateCheckerParameters, ParamsSerializer

def rate_query(params, data_load_testing=False):
    """ params is a method parameter of type RateCheckerParameters."""

    # the precalculated results are done by favoring negative points over positive ones
    # and the API does the opposite
    factor = 1
    if data_load_testing:
        factor = -1

    region_ids = Region.objects.filter(
        state_id=params.state).values_list('region_id', flat=True)

    rates = Rate.objects.filter(
        region_id__in=region_ids,
        product__loan_purpose=params.loan_purpose,
        product__pmt_type=params.rate_structure,
        product__loan_type=params.loan_type,
        product__max_ltv__gte=params.max_ltv,
        product__loan_term=params.loan_term,
        product__max_loan_amt__gte=params.loan_amount,
        product__max_fico__gte=params.maxfico,
        product__min_fico__lte=params.minfico)

    if params.loan_type != 'FHA-HB':
        rates = rates.filter(product__min_loan_amt__lte=params.loan_amount)

    if params.rate_structure == 'ARM':
        rates = rates.filter(
            product__int_adj_term=params.arm_type[:-2],
            product__io=params.io)

    if data_load_testing:
        rates = rates.filter(
            product__institution=params.institution,
            lock=params.max_lock)
    else:
        rates = rates.filter(
            lock__lte=params.max_lock,
            lock__gt=params.min_lock)

    deduped_rates = rates.values_list('product__plan_id', 'region_id').distinct()
    product_ids = [p[0] for p in deduped_rates]

    adjustments = Adjustment.objects.filter(product__plan_id__in=product_ids).filter(
        Q(max_loan_amt__gte=params.loan_amount) | Q(max_loan_amt__isnull=True),
        Q(min_loan_amt__lte=params.loan_amount) | Q(min_loan_amt__isnull=True),
        Q(prop_type=params.property_type) | Q(prop_type__isnull=True) | Q(prop_type=""),
        Q(state=params.state) | Q(state__isnull=True) | Q(state=""),
        Q(max_fico__gte=params.maxfico) | Q(max_fico__isnull=True),
        Q(min_fico__lte=params.minfico) | Q(min_fico__isnull=True),
        Q(min_ltv__lte=params.min_ltv) | Q(min_ltv__isnull=True),
        Q(max_ltv__gte=params.max_ltv) | Q(max_ltv__isnull=True),
    ).values('product_id', 'affect_rate_type').annotate(sum_of_adjvalue=Sum('adj_value'))

    summed_adj_dict = {}
    for adj in adjustments:
        current = summed_adj_dict.get(adj['product_id'], {})
        current[adj['affect_rate_type']] = adj['sum_of_adjvalue']
        summed_adj_dict[adj['product_id']] = current
    available_rates = {}
    data_timestamp = ""
    for rate in rates:
        #TODO: check that it the same all the time, and do what if it is not?
        data_timestamp = rate.data_timestamp
        product = summed_adj_dict.get(rate.product_id, {})
        rate.total_points += product.get('P', 0)
        rate.base_rate += product.get('R', 0)
        distance = abs(params.points - rate.total_points)
        if float(distance) > 0.5:
            continue
        if rate.product_id not in available_rates:
            available_rates[rate.product_id] = rate
        else:
            current_difference = abs(params.points - available_rates[rate.product_id].total_points)
            new_difference = abs(params.points - rate.total_points)
            if new_difference < current_difference or (
                    new_difference == current_difference and
                    factor * available_rates[rate.product_id].total_points < 0 and
                    factor * rate.total_points > 0):
                available_rates[rate.product_id] = rate

    data = {}
    for rate in available_rates:
        key = str(available_rates[rate].base_rate)
        current_value = data.get(key, 0)
        if data_load_testing:
            data[key] = "%s" % available_rates[rate].total_points
        else:
            data[key] = current_value + 1

    if not data:
        obj = Region.objects.all()[0]
        data_timestamp = obj.data_timestamp

    return {'data': data, 'timestamp': data_timestamp}


@api_view(['GET'])
def rate_checker(request):
    """ Return available rates in percentage and number of institutions with the corresponding rate (i.e. "4.75": 2 means there are 2 institutions with the rate of 4.75%)"""

    if request.method == 'GET':

        # Clean the parameters, make sure no leading or trailing spaces, transform them to upper cases
        fixed_data = dict(map(lambda (k,v): (k, v.strip().upper()), request.QUERY_PARAMS.iteritems()))
        serializer = ParamsSerializer(data=fixed_data)


        if serializer.is_valid():
            serializer.calculate_data()
            parameters = RateCheckerParameters()
            try:
                #parameters.set_from_query_params(request.QUERY_PARAMS)
                #rate_results = rate_query(parameters)
                rate_results={}
                rate_results['request'] = serializer.data
            except KeyError as e:
                error_response = {'detail': str(e.args[0])}
                return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

            return Response(rate_results)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
