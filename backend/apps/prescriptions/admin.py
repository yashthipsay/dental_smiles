from django.contrib import admin
from .models import Medicine, Prescription, PrescriptionItem

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1
    min_num = 1
    validate_min = True
    autocomplete_fields = ['medicine']

    

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['get_user_full_name', 'doctor_name', 'get_items_count', 'issued_at']
    list_filter = ['issued_at', 'doctor_name']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name', 'doctor_name', 'notes']
    readonly_fields = ['issued_at']
    ordering = ['-issued_at']
    inlines = [PrescriptionItemInline]
    autocomplete_fields = ['user', 'appointment', 'treatment_plan']

    @admin.display(description="User")
    def get_user_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return 'N/A'
    get_user_full_name.short_description = 'User'

    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Medicines'

    def get_changeform_initial_data(self, request):
        """Pre-fill user, appointment, and treatment_plan from query parameters"""
        initial = super().get_changeform_initial_data(request)
        user_id = request.GET.get('user')
        appointment_id = request.GET.get('appointment')
        treatment_plan_id = request.GET.get('treatment_plan')
        
        if user_id:
            initial['user'] = user_id
        if appointment_id:
            initial['appointment'] = appointment_id
        if treatment_plan_id:
            initial['treatment_plan'] = treatment_plan_id
        
        return initial