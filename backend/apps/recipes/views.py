from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def recipe_home(request):
    return HttpResponse("Recipes Home")