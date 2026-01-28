from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

app_name = "reviews"

urlpatterns = [
    path("", views.ReviewList.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)