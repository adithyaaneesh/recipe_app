from django.urls import path
from . import views

urlpatterns = [
    path('', views.interactions_home, name='interactions_home'),
]