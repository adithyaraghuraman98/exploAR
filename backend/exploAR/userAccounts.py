# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse
import requests
from django.http import HttpResponse, Http404
from configparser import ConfigParser
import os

# Create your views here.
    