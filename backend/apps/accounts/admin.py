from django.contrib import admin
from unfold.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.urls import reverse, path
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from .models import User, StudentProfile
from ..prescriptions.models import Prescription

# Unregister the default Group admin and re-register with Unfold styling
admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    
    # Adding prescriptions here
    list_display = ['phone_number', 'get_full_name', 'email', 'is_student', 'get_prescriptions', 'latest_prescription', 'create_prescription_button', 'is_active', 'created_at']
    list_filter = ['is_student', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['phone_number', 'first_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at', 'get_prescriptions', 'latest_prescription', 'create_prescription_button']
    fieldsets = (
        ('Personal Info', {
            'fields': ('phone_number', 'first_name', 'last_name', 'email', 'age', 'birth_date')
        }),
        ('Prescriptions', {
            'fields': ('get_prescriptions', 'latest_prescription', 'create_prescription_button')
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

    def get_prescriptions(self, obj):
        prescriptions = Prescription.objects.filter(user=obj)
        if prescriptions:
            url = reverse('admin:prescriptions_prescription_changelist')
            return format_html(
                '<a href="{}?user__id__exact={}">View previous {} prescriptions</a>',
                url,
                obj.pk,
                prescriptions.count()
            )
        return "No prescriptions"
        get_prescriptions.short_description = 'Prescriptions'

    def latest_prescription(self, obj):
        latest = Prescription.objects.filter(user=obj).order_by('-issued_at').first()
        if latest:
            url = reverse('admin:prescriptions_prescription_change', args=[latest.pk])
            return format_html(
                '<a href="{}">Prescription {} - {}</a>',
                url,
                latest.id,
                latest.issued_at.strftime("%Y-%m-%d"),
            )
        return "No prescriptions"
    latest_prescription.short_description = 'Latest Prescription'

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    get_full_name.short_description = 'Full Name'

    def create_prescription_button(self, obj):
        button = format_html(
            '<a class="button" href="{}?user={}">Create Prescription</a>',
            reverse('admin:prescriptions_prescription_add'),
            obj.pk
        )
        return button

@admin.register(StudentProfile)
class StudentProfileAdmin(ModelAdmin):
    list_display = ['user', 'college_name', 'student_id', 'verified', 'verified_at']
    list_filter = ['verified', 'verified_at']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name', 'college_name', 'student_id']
    readonly_fields = ['verified_at']
     
