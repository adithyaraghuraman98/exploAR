# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from django.contrib.auth.models import User
import uuid
import json

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User)
    scout = models.ManyToManyField("Profile")
    latitude = models.DecimalField(null = True, max_digits=8, decimal_places=6)
    longitude = models.DecimalField(null = True, max_digits=9, decimal_places=6)

class Review(models.Model):
    google_place_id = models.TextField(blank=False)
    reviewer = models.ForeignKey(User)
    review_text = models.CharField(max_length=1000, blank = True)
    created_at = models.DateTimeField()

class Place(models.Model):
    google_place_id = models.TextField(blank=False)
    name = models.TextField(blank= False)
    latitude = models.DecimalField(blank = False, max_digits=8, decimal_places=6)
    longitude = models.DecimalField(blank = False, max_digits=9, decimal_places=6)
    address = models.TextField(blank = True)
    open_now = models.NullBooleanField(null = True, blank = True)
    open_hours = models.TextField(blank = True)
    website = models.TextField(blank = True)
    google_rating = models.DecimalField(blank = True, max_digits=2, decimal_places=1)
    phone_number = models.TextField(blank = True)
    photo = models.ImageField(blank = True)

    def set_open_hours(self,x):
        self.open_hours = json.dumps(x)

    def get_open_hours(self):
        return json.loads(self.open_hours)
    
