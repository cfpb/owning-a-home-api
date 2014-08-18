from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from countylimits.models import CountyLimit

from django.db.utils import OperationalError


@api_view(['GET'])
def county_limits(request):
    """ Return all counties with their limits per state. """
    if request.method == 'GET':
        package = {'request': {}, 'data': []}
        if 'state' in request.GET:
            try:
                state = package['request']['state'] = request.GET['state']
                package['data'] = CountyLimit.county_limits_by_state(state)
            except OperationalError as e:
                error_response = {'detail': 'DB server is not available'}
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except KeyError as e:
                error_response = {'detail': 'An error happened while using %s' % e.args[1]}
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(package)
        else:
            return Response({'detail': 'Required parameter state is missing'}, status=status.HTTP_400_BAD_REQUEST)
