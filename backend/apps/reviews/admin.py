from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__phone_number', 'user__full_name', 'comment']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
