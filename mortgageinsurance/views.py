from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from mortgageinsurance.models import MonthlyMortgageIns


@api_view(['GET'])
def mortgage_insurance(request):
    """ Return the monthly and upfront mortgage insurance premiums in percentages (i.e. 1.7% returns 1.7) """
    if request.method == 'GET':
        package = {'request': {}, 'data': []}
        package['data'] = { 'monthly' : 0, 'upfront' : 0 }
        return Response(package)
        # if 'state' in request.GET:
        #     state = package['request']['state'] = request.GET['state']
        #     package['data'] = CountyLimit.county_limits_by_state(state)
        #     return Response(package)
        # else:
        #     return Response({'detail': 'Required parameter state is missing'}, status=status.HTTP_400_BAD_REQUEST)
