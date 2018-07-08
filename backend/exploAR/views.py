# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core import serializers
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.db.models import Q

import datetime
import requests
from django.http import HttpResponse, Http404
from configparser import ConfigParser
import os
import json
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db import transaction

from exploAR.models import Profile, Review, Place
from exploAR.forms import RegistrationForm, ReviewForm

# Create your views here.
def home(request):

    context = {}
    if 'place-id' in request.POST:
        context['placeID'] = request.POST['place-id']

    return render(request,'exploAR/home.html',context)    

def get_API_Keys():

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = ConfigParser()
    config.read(os.path.join(BASE_DIR, 'config.ini'))
    google_api_key = config.get('API_KEYS', 'Google_Places')
    yelp_api_key = config.get('API_KEYS', 'Yelp')
    return (google_api_key, yelp_api_key)

def is_valid_coordinate(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

@transaction.atomic
def get_places_json(request):

    google_api_key = get_API_Keys()[0]
    if (not 'lat' in request.GET) or (not 'lng' in request.GET):
        print("Lat and long not found")
        return JsonResponse({'status':'false','message':"Lat and long not received"}, status=400)
    if((not is_valid_coordinate(request.GET['lat'])) or (not is_valid_coordinate(request.GET['lng'])) or 
        (float(request.GET['lat']) < -90) or (float(request.GET['lat']) > 90) or 
        (float(request.GET['lng']) < -180) or (float(request.GET['lng']) > 180)):
        return JsonResponse({'status':'false','message':"Lat and long are invalid"}, status=400)

    lat = request.GET['lat']
    lng = request.GET['lng']

    if request.user.username:
        request.user.profile.latitude = lat
        request.user.profile.longitude = lng
        request.user.profile.save()
    
    category = None
    if ('category' in request.GET):
        category = request.GET['category']

    googleResp = get_google_info(lat, lng, category, google_api_key).json()
    outList = []
    
    for result in googleResp["results"]:
        p = processResult(result)
        outList.append(p)
    
    responseText = serializers.serialize('json', outList, use_natural_foreign_keys=True, use_natural_primary_keys=True)
    return HttpResponse(responseText, content_type='application/json')


def processResult(result):
    
    google_place_id = result["place_id"] if "id" in result else ""
    name = result["name"] if "name" in result else ""
    latitude = result["geometry"]["location"]["lat"]
    longitude = result["geometry"]["location"]["lng"]
    address = result["vicinity"] if "vicinity" in result else "No Address found"

    open_now = "Open information not available"

    if "opening_hours" in result:
        if "open_now" in result["opening_hours"]:
            open_now = result["opening_hours"]["open_now"]

        if open_now:
            open_now = "Yes"
        else:
            open_now = "No"
    
    google_rating = result["rating"] if "rating" in result else 0
    p = Place(google_place_id = google_place_id, name = name,
        latitude = latitude, longitude = longitude, address = address, 
        open_now = open_now, google_rating = google_rating)    
    
    return p

def get_google_info(lat, lng, category, API_KEY, criteria = 'distance'):
    
    location = str(lat) + "," + str(lng)
    types = category
    key = API_KEY
    url = '''https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%s&type=%s&key=%s&rankby=%s'''%(location,types,key,criteria)
    response = requests.get(url)
    return response

def get_yelp_info(lat, lng, API_KEY):
    
    headers = {
        'Authorization': 'Bearer %s' % API_KEY
    }
    params = {
        'latitude': lat, 'longitude':lng
    }

    response = requests.get('https://api.yelp.com/v3/businesses/search',
        headers = headers, params = params)

    return response

def getOpenHours(periods):
    
    out = [None for i in range(7)]
    
    for period in periods:
        openTime = period["open"]["time"]
        closeTime = period["close"]["time"] if "close" in period else None
        out[period["open"]["day"]] = openTime+"-"+closeTime
    
    return out

def getPhoto(key, photo_ref, max_height = 512):
    
    url = '''https://maps.googleapis.com/maps/api/place/photo?maxheight=%s&photoreference=%s&key=%s'''%(max_height,photo_ref,key)
    response = requests.get(url)
    return response

def get_google_reviews(response):
    
    out = []

    if "reviews" in response:
        for review in response["reviews"]:
            out_review = {'reviewer_name': review["author_name"],
            'review_time': datetime.datetime.fromtimestamp(int(review["time"])).strftime('%c'),
             'review_text': review["text"]}
            out.append(out_review)      
    
    return out

def get_place_details_json(request):
    
    google_api_key = get_API_Keys()[0]

    place_id = ""

    if request.method == 'POST':
        place_id = request.POST['place-id']

    else:
        place_id = request.GET['place_id']
    
    url = '''https://maps.googleapis.com/maps/api/place/details/json?placeid=%s&key=%s'''%(place_id, google_api_key)  
    response = requests.get(url).json()
 
    if "result" in response:
        result = response["result"]
    else:
        return render(request,'exploAR/search.html', {'error': "No results found"})

    p = processResult(result)
    p.website = result["website"] if "website" in result else "No Website available"
    p.phone_number = result["formatted_phone_number"] if "formatted_phone_number" in result else "No Phone Number available"
    p.open_hours = getOpenHours(result["opening_hours"]["periods"]) if "opening_hours" in result else ["No hours information available" for i in range(7)]
    p.photo = getPhoto(google_api_key, result["photos"][0]["photo_reference"]) if "photos" in result else "No Image found"
    reviews = get_google_reviews(result)
    
    return ([p], reviews)

@login_required
@transaction.atomic
def addScout(request, id):
    
    if(int(id)>0 and int(id) <= len(Profile.objects.all())):
    
        p = Profile.objects.get(id=id)

        if p.user.username != request.user.username:
            request.user.profile.scout.add(p)
            request.user.profile.save()
            return redirect(reverse('profilePage', kwargs={"username": p.user.username}))
    
    return redirect(reverse('profilePage', kwargs={"username": request.user.username}))

@login_required
@transaction.atomic
def removeScout(request, id):

    if(int(id)>0 and int(id)<= len(Profile.objects.all())):

        p = Profile.objects.get(id=id)

        if p.user.username != request.user.username:
            request.user.profile.scout.remove(p)
            request.user.profile.save()
            return redirect(reverse('profilePage', kwargs={"username": p.user.username}))

    return redirect(reverse('profilePage', kwargs={"username": request.user.username}))

@transaction.atomic
def get_complete_place_info(request):

    place_id = ""

    if request.method == "GET":
        if (not 'place_id' in request.GET):
            print("Place_id not found")
            return JsonResponse({'status':'false','message':"Lat and long not received"}, status=400)
        place_id = request.GET['place_id']
    else:
        if (not 'place-id' in request.POST):
            print("Place_id not found")
            return JsonResponse({'status':'false','message':"Lat and long not received"}, status=400)
        place_id = request.POST['place-id']

    (google_resp, google_reviews) = get_place_details_json(request)

    reviews = Review.objects.all().filter(google_place_id=place_id).order_by('-created_at')
    responseText = {'google': google_resp, 'reviews':reviews, 'google_reviews': google_reviews}

    return responseText


@login_required
@transaction.atomic
def search_users(request):
    if('search-string' not in request.POST):
        return render(request, 'exploAR/searchScouts.html', {})

    search = request.POST['search-string'].split(" ")

    first_name = ""
    last_name = ""

    if len(search) > 1:
        first_name = search[0]
        last_name = search[1]
    elif len(search) == 1:
        first_name = search[0]

    profiles = Profile.objects.all().filter(Q(user__first_name = first_name) | Q(user__last_name = last_name))
    context = {"matches": profiles, "numMatches": len(profiles)}

    return render(request, 'exploAR/searchScouts.html', context)

def search(request):
    return render(request, 'exploAR/search.html', {})

def place_info(request):
    
    placeID = ""

    if request.method == "GET":
        if 'place_id' not in request.GET:
            return redirect(reverse('search'))
        placeID = request.GET['place_id']
    else:
        if 'place-id' not in request.POST:
            return redirect(reverse('search'))
        placeID = request.POST['place-id']

    print("placeID ", placeID, type(placeID))

    if (not placeID) or (placeID == "") or (placeID == "undefined"):
        return redirect(reverse('search'))

    response = get_complete_place_info(request)

    return render(request, 'exploAR/place_info.html', response)

@transaction.atomic
def register(request):
    context = {}

    # Just display the registration form if this is a GET request.
    if request.method == 'GET':
        context['form'] = RegistrationForm()
        return render(request, 'exploAR/register.html', context)

    # Creates a bound form from the request POST parameters and makes the 
    # form available in the request context dictionary.
    form = RegistrationForm(request.POST)
    context['form'] = form

    # Validates the form.
    if not form.is_valid():
        return render(request, 'exploAR/register.html', context)

    # At this point, the form data is valid.  Register and login the user.
    new_user = User.objects.create_user(username=form.cleaned_data['username'], 
                                        password=form.cleaned_data['password1'],
                                        email=form.cleaned_data['email'],
                                        first_name=form.cleaned_data['first_name'],
                                        last_name=form.cleaned_data['last_name'])
    

    new_profile = Profile.objects.create(user = new_user)
    new_user.save()
    new_profile.save()
    # Logs in the new user and redirects to his/her todo list
    new_user = authenticate(username=form.cleaned_data['username'],
                            password=form.cleaned_data['password1'])
    login(request, new_user)
    return redirect(reverse('home'))

def get_destination_json(request):
    
    google_api_key = get_API_Keys()[0]
    
    if (not 'place_id' in request.GET):
        print("Place id not found")
        return JsonResponse({'status':'false','message':"Place ID not received"}, status=400)

    response = get_complete_place_info(request)
    responseText = serializers.serialize('json', response['google'], use_natural_foreign_keys=True, use_natural_primary_keys=True)
    
    return HttpResponse(responseText, content_type='application/json')
    
@login_required
@transaction.atomic
def createReview(request):

    if 'place-id' not in request.POST:
        return

    place_id = request.POST['place-id']

    review = Review(reviewer = request.user, google_place_id = place_id,
        created_at = timezone.now())
    review_form = ReviewForm(request.POST, instance=review)

    if not review_form.is_valid():
        
        context = get_complete_place_info(request)
        return render(request, 'exploAR/place_info.html', context)

    review_form.save()
    review.save()
    
    context = get_complete_place_info(request)
    return render(request, 'exploAR/place_info.html', context)

@login_required
@transaction.atomic
def profilePage(request, username):

    context = {}

    userObj = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=userObj)
    userProfile = get_object_or_404(Profile, user=request.user)

    context['followingCount'] = profile.scout.count()
    context['profile'] = profile
    context['following'] = profile.scout.all()

    if userObj.username == request.user.username:
        return render(request, 'exploAR/profile_page.html', context)

    else:       

        if profile in userProfile.scout.all():
            context['followingUser'] = True
        else:
            context['followingUser'] = False

        return render(request, 'exploAR/profilePageOther.html', context)

@login_required
@transaction.atomic
def get_scouts_json(request):

    user = request.user
    out = []

    for p in user.profile.scout.all():
        out.append(p)

    responseText = serializers.serialize('json', out, use_natural_foreign_keys=True, use_natural_primary_keys=True)
    return HttpResponse(responseText, content_type='application/json')
    

def home_friends(request):

    return render(request,'exploAR/home_friends.html', {}) 


