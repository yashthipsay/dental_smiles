from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['phone_number', 'get_full_name', 'email', 'is_student', 'is_active', 'created_at']
    list_filter = ['is_student', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['phone_number', 'first_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Personal Info', {
            'fields': ('phone_number', 'first_name', 'last_name', 'email', 'age', 'birth_date')
        }),
        ('Permissions',  {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    get_full_name.short_description = 'Full Name'

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'college_name', 'student_id', 'verified', 'verified_at']
    list_filter = ['verified', 'verified_at']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name', 'college_name', 'student_id']
    readonly_fields = ['verified_at']
     
