from django.contrib import admin
from .models import Prescription

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['get_user_full_name', 'doctor_name', 'issued_at']
    list_filter = ['issued_at', 'doctor_name']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name', 'doctor_name', 'notes']
    readonly_fields = ['issued_at']
    ordering = ['-issued_at']

    def get_user_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return 'N/A'
    get_user_full_name.short_description = 'User'