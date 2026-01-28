from django.urls import path
from .views import Prescriptions

app_name = 'prescriptions'

urlpatterns = [
    path('', Prescriptions.as_view(), name='prescription')
]