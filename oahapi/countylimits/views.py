from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from countylimits.models import CountyLimit


@api_view(['GET'])
def county_limits(request):
    """ Return all counties with their limits per state. """
    if request.method == 'GET':
        package = {'request': {}, 'errors': [], 'data': [], 'status': 'Ok'}
        if 'state' in request.GET:
            state = package['request']['state'] = request.GET['state']
            package['data'] = CountyLimit.county_limits_by_state(state)
        return Response(package)
