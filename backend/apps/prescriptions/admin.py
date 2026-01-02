from django.contrib import admin
from .models import Prescription

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['get_user_full_name', 'doctor_name', 'issued_at']
    list_filter = ['issued_at', 'doctor_name']
    search_fields = ['user__phone_number', 'user__full_name', 'doctor_name', 'notes']
    readonly_fields = ['issued_at']
    ordering = ['-issued_at']

    def get_user_full_name(self, obj):
        return obj.user.full_name
    get_user_full_name.short_description = 'User'