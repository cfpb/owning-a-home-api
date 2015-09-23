from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from countylimits.models import CountyLimit


@api_view(['GET'])
def county_limits(request):
    """ Return all counties with their limits per state. """
    if request.method == 'GET':
        package = {'request': {}, 'data': []}
        if 'state' in request.GET:
            state = request.GET['state']
            data = CountyLimit.county_limits_by_state(state)
            if data:
                package['request']['state'] = request.GET['state']
                package['data'] = data
                return Response(package)
            else:
                return Response({'state': 'Invalid state'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': 'Required parameter state is missing'}, status=status.HTTP_400_BAD_REQUEST)
