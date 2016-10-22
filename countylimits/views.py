from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from countylimits.models import CountyLimit, State

SAFE_STATE_LIST = (  # states can be specified by abbreviation or FIPS code
    list(State.objects.values_list('state_abbr', flat=True)) +
    list(State.objects.values_list('state_fips', flat=True))
    )


@api_view(['GET'])
def county_limits(request):
    """ Return all counties with their limits per state. """
    if request.method == 'GET':
        package = {'request': {}, 'data': []}
        if 'state' in request.GET:
            state = request.GET['state']
            if state in SAFE_STATE_LIST:
                data = CountyLimit.county_limits_by_state(state)
                package['request']['state'] = state
                package['data'] = data
                return Response(package)
            else:
                return Response(
                    {'state': 'Invalid state'},
                    status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {'detail': 'Required parameter state is missing'},
                status=status.HTTP_400_BAD_REQUEST)
