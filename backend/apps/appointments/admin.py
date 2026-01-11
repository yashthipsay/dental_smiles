from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.utils import timezone
from .models import AppointmentRequest, Appointment, TreatmentSession, TreatmentPlan
from .notification_service import send_treatment_session_notification

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['get_user_full_name', 'get_user_phone_number', 'scheduled_at', 'status', 'created_at']
    list_filter = ['status', 'scheduled_at', 'created_at']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-scheduled_at']
    autocomplete_fields = ['user']

    fieldsets = (
        ('Patient Information', {
            'fields': ('user',)
        }),
        ('Appointment Details', {
            'fields': ('scheduled_at', 'status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_user_full_name(self, obj):
        if obj.user:
            name = [obj.user.first_name if obj.user.first_name else '', obj.user.last_name if obj.user.last_name else '']
            return ' '.join(name).strip()
        return 'N/A'
    
    get_user_full_name.short_description = 'Full Name'

    def get_user_phone_number(self, obj):
        return obj.user.phone_number if obj.user else 'N/A'
    get_user_phone_number.short_description = 'Phone Number'

    def get_changeform_initial_data(self, request):
        """Pre-fill user from query parameter"""
        initial = super().get_changeform_initial_data(request)
        user_id = request.GET.get('user')
        request_id = request.GET.get('request_id')
        
        if user_id:
            initial['user'] = user_id
        
        if request_id:
            request.session['appointment_request_id'] = request_id
        
        return initial

    def save_model(self, request, obj, form, change):
        """Auto-confirm the appointment request after creating appointment"""
        super().save_model(request, obj, form, change)
        
        # Update appointment request status to approved
        request_id = request.session.pop('appointment_request_id', None)
        if request_id:
            try:
                appointment_request = AppointmentRequest.objects.get(pk=request_id)

                if obj.status == 'canceled':
                    appointment_request.status = 'canceled'
                    status_message = 'canceled'
                else:
                    appointment_request.status = 'confirmed'
                    status_message = 'confirmed'

                appointment_request.save()
                self.message_user(
                    request,
                    f"Appointment request for {appointment_request.user.first_name} {appointment_request.user.last_name} has been {status_message}."
                )
            except AppointmentRequest.DoesNotExist:
                pass

    class Media:
        js = ('admin/js/appointment_admin.js',)


@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'treatment_type', 'total_amount', 'amount_paid', 'estimated_duration_months', 'is_completed', 'created_at']
    list_filter = ['treatment_type', 'is_completed', 'created_at']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def get_full_name(self, obj):
        if obj.user:
            name = [obj.user.first_name if obj.user.first_name else '', obj.user.last_name if obj.user.last_name else '']
            return ' '.join(name).strip()
        return 'N/A'

@admin.register(TreatmentSession)
class TreatmentSessionAdmin(admin.ModelAdmin):
    list_display = ['get_user_name', 'get_treatment_type', 'session_number', 'scheduled_at', 'notification_status', 'notify_button']
    list_filter = ['treatment_plan__treatment_type', 'scheduled_at', 'notification_sent']
    search_fields = ['treatment_plan__user__phone_number', 'treatment_plan__user__first_name', 'treatment_plan__user__last_name']
    readonly_fields = ['session_number', 'created_at', 'updated_at', 'notification_sent', 'notified_at']

    fieldsets = (
        ('Treatment Session Info', {
            'fields': ('treatment_plan', 'session_number', 'amount_for_session', 'amount_received', 'description')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'completed_at')
        }),
        ('Notifications', {
            'fields': ('notification_sent', 'notified_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_user_name(self, obj):
        if obj.treatment_plan and obj.treatment_plan.user:
            name = [obj.treatment_plan.user.first_name if obj.treatment_plan.user.first_name else '', obj.treatment_plan.user.last_name if obj.treatment_plan.user.last_name else '']
            return ' '.join(name).strip()
        return 'N/A'
    get_user_name.short_description = 'Patient'

    def get_treatment_type(self, obj):
        return obj.treatment_plan.get_treatment_type_display()
    get_treatment_type.short_description = 'Treatment Type'

    def notification_status(self, obj):
        if obj.notification_sent:
            return format_html(
                '<span style="color: green; font-weight: bold;">Sent</span><br><small>{}</small>',
                obj.notified_at.strftime('%Y-%m-%d %H:%M') if obj.notified_at else ''
            )
        return format_html('<span style="color: red; font-weight: bold;">Not Sent</span>')
    notification_status.short_description = 'Notification Status'

    def notify_button(self, obj):
        if not obj.notification_sent:
            return format_html(
                '<a class="button" href="{}">Notify on WhatsApp</a>',
                reverse('admin:send-treatment-session-notification', args=[obj.pk])
            )
        return format_html('<span style="color: gray;">Already Sent</span>')
    notify_button.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:session_id>/notify/',
                self.admin_site.admin_view(self.send_notification_action),
                name='send-treatment-session-notification'
            ),
        ]
        return custom_urls + urls
    
    def send_notification_action(self, request, session_id):
        """Custom admin action to send WhatsApp notification"""
        try:
            treatment_session = TreatmentSession.objects.get(pk=session_id)
            response = send_treatment_session_notification(treatment_session)


            self.message_user(
                request,
                f"WhatsApp ntification sent to {treatment_session.treatment_plan.user.first_name} {treatment_session.treatment_plan.user.last_name}."
            )
        except TreatmentSession.DoesNotExist:
            self.message_user(request, "Treatment session not found", level='error')

        return HttpResponseRedirect(
            reverse('admin:appointments_treatmentsession_changelist')
        )
    
# Readonly admin for AppointmentRequest
@admin.register(AppointmentRequest)
class AppointmentRequestAdmin(admin.ModelAdmin):
    list_display = ['get_user_full_name', 'get_user_phone_number', 'created_at', 'status', 'source', 'create_appointment_button', 'created_at']
    list_filter = ['status', 'source', 'created_at']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name']
    readonly_fields = ['user', 'created_at', 'updated_at', 'source']
    ordering = ['-created_at']

    def get_user_full_name(self, obj):
        if obj.user:
            name = [obj.user.first_name if obj.user.first_name else '', obj.user.last_name if obj.user.last_name else '']
            return ' '.join(name).strip()
        return 'N/A'
    get_user_full_name.short_description = 'Patient Name'

    def get_user_phone_number(self, obj):
        return obj.user.phone_number
    get_user_phone_number.short_description = 'Phone Number'

    def create_appointment_button(self, obj):
        """ Display button to create appointment from request"""
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}?user={}&request_id={}">Create Appointment</a>',
                reverse('admin:appointments_appointment_add'),
                obj.user.pk,
                obj.pk
            )
        elif obj.status == 'confirmed':
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Confirmed</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Rejected</span>'
            )
    create_appointment_button.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:request_id>/create-appointment/',
                self.admin_site.admin_view(self.create_appointment_view),
                name='create-appointment-from-request'
            )
        ]
        return custom_urls + urls
    
    def create_appointment_view(self, request, request_id):
        """Redirect to appointment creation with pre-filled user data"""
        try:
            appointment_request = AppointmentRequest.objects.get(pk=request_id)
            return HttpResponseRedirect(
                f"{reverse('admin:appointments_appointment_add')}?user={appointment_request.user.pk}&request_id={request_id}"
            )
        except AppointmentRequest.DoesNotExist:
            self.message_user(request, "Appointment request not found", level='error')
            return HttpResponseRedirect(reverse('admin:appointments_appointmentrequest_changelist'))