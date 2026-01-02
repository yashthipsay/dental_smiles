from django.contrib import admin

from django.contrib import admin

from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'scheduled_at', 'status', 'created_at']
    list_filter = ['status', 'scheduled_at', 'created_at']
    search_fields = ['user__phone_number', 'user__full_name']
    readonly_fields = ['created_at']
    ordering = ['-scheduled_at']
