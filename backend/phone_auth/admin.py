from django.contrib import admin
from .models import PhoneOTP

@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'is_verified', 'otp_created_at', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__email', 'phone_number']
    readonly_fields = ['uid', 'created_at', 'updated_at']