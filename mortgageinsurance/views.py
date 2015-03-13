from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from mortgageinsurance.models import MonthlyMortgageIns
from mortgageinsurance.ParamsSerializer import ParamsSerializer


@api_view(['GET'])
def mortgage_insurance(request):
    """ Return the monthly and upfront mortgage insurance premiums in percentages (i.e. 1.7% returns 1.7) """
    if request.method == 'GET':
        print request.QUERY_PARAMS

        loan_type = request.QUERY_PARAMS.get('loan_type')
        rate_structure = request.QUERY_PARAMS.get('rate_structure')
        va_status = request.QUERY_PARAMS.get('va_status')

        data = {
                'price' : request.QUERY_PARAMS.get('price'),
                'loan_amount' : request.QUERY_PARAMS.get('loan_amount'),
                'minfico' : request.QUERY_PARAMS.get('minfico'),
                'maxfico' : request.QUERY_PARAMS.get('maxfico'),
                'loan_term' : request.QUERY_PARAMS.get('loan_term'),
                'loan_type' : '' if loan_type is None else loan_type.strip().upper(),
                'rate_structure' : '' if rate_structure is None else rate_structure.strip().upper(),
                'va_status' : '' if va_status is None else va_status.strip().upper(),
        }
        # params = Params(price=request.QUERY_PARAMS.get('price'),
        #                 loan_amount=request.QUERY_PARAMS.get('loan_amount'),
        #                 minfico=request.QUERY_PARAMS.get('minfico'),
        #                 maxfico=request.QUERY_PARAMS.get('maxfico'),
        #                 loan_term=request.QUERY_PARAMS.get('loan_term'),
        #                 va_status=request.QUERY_PARAMS.get('va_status'))
        # serializer = ParamsSerializer(params)
        serializer = ParamsSerializer(data=data)
        is_valid = serializer.is_valid()
        print is_valid
        print "errors: "
        print serializer.errors
        # True
        #print serializer.validated_data
        # {'content': 'foo bar', 'email': 'leila@example.com', 'created': datetime.datetime(2012, 08, 22, 16, 20, 09, 822243)}

        print serializer.data
        print(repr(serializer))
        # print serializer.validated_data
        #return Response(package)
        # if 'state' in request.GET:
        #     state = package['request']['state'] = request.GET['state']
        #     package['data'] = CountyLimit.county_limits_by_state(state)
        #     return Response(package)
        # else:
        #     return Response({'detail': 'Required parameter state is missing'}, status=status.HTTP_400_BAD_REQUEST)
        if is_valid:
            package = {}
            package['request'] = serializer.data
            package['data'] = {
                                'monthly' : MonthlyMortgageIns.get_avg_premium(serializer.data),
                                'upfront' : 0.0, # Will replace with UpfrontMortgageIns.get_avg_premium(serializer.data) when ready
                               }
            return Response(package)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

