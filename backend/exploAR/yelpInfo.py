# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse
import requests
from django.http import HttpResponse, Http404
from configparser import ConfigParser
import os

def get_yelp_info(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = ConfigParser()
    config.read(os.path.join(BASE_DIR, 'config.ini'))
    API_KEY = config.get('API_KEYS', 'Yelp')
    
    if (not 'lat' in request.GET) or (not 'lng' in request.GET):
        print("Lat and long not found")
        return JsonResponse({'status':'false','message':"Lat and long not received"}, status=400)
    
    lat = request.GET['lat']
    lng = request.GET['lng']
    

    headers = {
        'Authorization': 'Bearer %s' % API_KEY
    }
    params = {
        'latitude': lat, 'longitude':lng
    }

    response = requests.get('https://api.yelp.com/v3/businesses/search',
        headers = headers, params = params)

    return HttpResponse(response, content_type='application/json')



