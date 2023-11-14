"""
URL configuration for 'calc' app
"""

from django.urls import path
from .views import HomePageView
from . import views

#Handle routing for calc app
urlpatterns = [
    path("", HomePageView.as_view(), name = "home"),
    path("postinput/", views.receive_form, name = "postform"),
]
