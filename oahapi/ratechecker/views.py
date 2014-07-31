from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.

@api_view(['GET'])
def fake_list(request):
    if request.method == 'GET':
        return Response({'a':1})
