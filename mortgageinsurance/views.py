from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

import math

from mortgageinsurance.models import Monthly, Upfront
from mortgageinsurance.params_serializer import ParamsSerializer


@api_view(['GET'])
def mortgage_insurance(request):
    """ Return the monthly and upfront mortgage insurance premiums in percentages (i.e. 1.7% returns 1.7) 
        If no premiums were found, no data will be returned. """

    if request.method == 'GET':

        # Clean the parameters, make sure no leading or trailing spaces, transform them to upper cases
        fixed_data = dict(map(lambda (k, v): (k, v.strip().upper()), request.QUERY_PARAMS.iteritems()))

        serializer = ParamsSerializer(data=fixed_data)

        if serializer.is_valid():
            package = {}
            package['request'] = serializer.data
            package['data'] = {}

            monthly = Monthly.get_avg_premium(serializer.data)
            upfront = Upfront.get_premium(serializer.data)

            if not math.isnan(monthly):
                package['data']['monthly'] = monthly

            if not math.isnan(upfront):
                package['data']['upfront'] = upfront

            return Response(package)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

