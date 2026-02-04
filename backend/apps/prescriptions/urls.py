from django.urls import path
from .views import Prescriptions, PrescriptionExists, PrescriptionPDFView

app_name = 'prescriptions'

urlpatterns = [
    path('', Prescriptions.as_view(), name='prescription'),
    path('exists/', PrescriptionExists.as_view(), name='prescription-exists'),
    path('send_pdf/', PrescriptionPDFView.as_view(), name='prescription-pdf'),
]