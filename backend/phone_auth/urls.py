from django.urls import path
from .views import (
    SendOTPView,
    VerifyOTPView,
    ResendOTPView,
    PhoneStatusView,
    IsAlreadyRegisteredView,
    IsProfileCompleteView,
)

app_name = 'phone_auth'

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('status/', PhoneStatusView.as_view(), name='phone-status'),
    path('is-registered/', IsAlreadyRegisteredView.as_view(), name='is-registered'),
    path('is-profile-complete/', IsProfileCompleteView.as_view(), name='is-profile-complete'),
]

