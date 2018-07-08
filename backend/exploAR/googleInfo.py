# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse
import requests
from django.http import HttpResponse, Http404
from configparser import ConfigParser
import os

def get_google_info(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = ConfigParser()
    config.read(os.path.join(BASE_DIR, 'config.ini'))
    API_KEY = config.get('API_KEYS', 'Google_Places')
    if (not 'lat' in request.GET) or (not 'lng' in request.GET):
        print("Lat and long not found")
        return JsonResponse({'status':'false','message':"Lat and long not received"}, status=400)
    
    lat = request.GET['lat']
    lng = request.GET['lng']
    

    category = None
    if ('category' in request.GET):
        category = request.GET['category']
    
    location = str(lat) + "," + str(lng)
    radius = 1600
    types = category
    key = API_KEY
    url = '''https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%s&radius=%s&types=%s&key=%s'''%(location,radius,types,key)
    response = requests.get(url)
    return HttpResponse(response, content_type='application/json')
