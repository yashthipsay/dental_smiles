from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.db.models import F
from django.template.response import TemplateResponse
from .models import AppointmentRequest, Appointment, TreatmentSession, TreatmentPlan
from .notification_service import send_treatment_session_notification
from ..prescriptions.models import Prescription

@admin.register(Appointment)
class AppointmentAdmin(ModelAdmin):
    list_display = ['get_user_full_name', 'get_user_phone_number', 'get_prescriptions','latest_prescription', 'create_prescription_button', 'scheduled_at', 'end_time', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'scheduled_at', 'created_at']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name']
    readonly_fields = ['get_prescriptions', 'latest_prescription', 'create_prescription_button', 'created_at', 'updated_at']
    ordering = ['-scheduled_at']
    autocomplete_fields = ['user']
    change_list_template = 'admin/appointments_changelist.html'

    fieldsets = (
        ('Patient Information', {
            'fields': ('user',)
        }),
        ('Appointment Details', {
            'fields': ('scheduled_at', 'end_time', 'status', 'payment_method', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_prescriptions(self, obj):
        prescriptions = Prescription.objects.filter(appointment=obj)
        if prescriptions:
            url = reverse('admin:prescriptions_prescription_changelist')
            return format_html(
                '<a href="{}?appointment__id__exact={}"> View previous {} prescriptions </a>',
                url,
                obj.pk,
                prescriptions.count()    
            )
        return "No prescriptions"
    get_prescriptions.short_description = 'Prescriptions'

    def latest_prescription(self, obj):
        latest = Prescription.objects.filter(appointment=obj).order_by('-issued_at').first()
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

    def create_prescription_button(self, obj):
        """Creates a prescription for that appointment and user"""
        button = format_html(
            '<a class="button" href="{}?user={}&appointment={}">Create Prescription</a>',
            reverse('admin:prescriptions_prescription_add'),
            obj.user.pk,
            obj.pk
        )
        return button

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "calender/",
                self.admin_site.admin_view(self.calender_view),
                name="appointments-calender",
            ),
        ]
        return custom_urls + urls
    
    def calender_view(self, request):
        appointments = Appointment.objects.all().values(
            'id', 
            'scheduled_at',
            'end_time',
            'status',
            user_name = F('user__first_name')
        )

        events = [
            {            
            'id': apt['id'],
            'title': f"{apt['user_name']} - {apt['status']}",
            'start': apt['scheduled_at'].isoformat(),
            'end': apt['end_time'].isoformat() if apt['end_time'] else None,
            'backgroundColor': '#0275d8' if apt['status'] == 'confirmed' else '#ffc107',
            }
            for apt in appointments
            if apt['scheduled_at']
        ]
        return TemplateResponse(
            request,
            "admin/appointments_calender.html",
            {'events': events}
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

    # def create_prescription_button(self, obj):

    #     if obj.user.prescription
    #     return format_html()

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
class TreatmentPlanAdmin(ModelAdmin):
    list_display = ['get_full_name', 'treatment_type', 'get_prescriptions', 'get_latest_prescription', 'create_prescription_button', 'total_amount', 'amount_paid', 'estimated_duration_months', 'is_completed', 'created_at']
    list_filter = ['treatment_type', 'is_completed', 'created_at']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name']
    readonly_fields = [ 'get_prescriptions', 'get_latest_prescription', 'created_at']
    ordering = ['-created_at']
    autocomplete_fields = ['user', 'initial_appointment']

    def get_full_name(self, obj):
        if obj.user:
            name = [obj.user.first_name if obj.user.first_name else '', obj.user.last_name if obj.user.last_name else '']
            return ' '.join(name).strip()
        return 'N/A'

    def get_prescriptions(self, obj):
        prescriptions = Prescription.objects.filter(treatment_plan=obj)
        if prescriptions:
            url = reverse('admin:prescriptions_prescription_changelist')
            return format_html(
                '<a href="{}?appointment__id__exact={}"> View previous {} prescriptions </a>',
                url,
                obj.initial_appointment.pk if obj.initial_appointment else '',
                prescriptions.count()    
            )
        return "No prescriptions"
    get_prescriptions.short_description = 'Prescriptions'    

    def get_latest_prescription(self, obj):
        latest = Prescription.objects.filter(treatment_plan=obj).order_by('-issued_at').first()
        user_prescriptions_count = Prescription.objects.filter(user=obj.user).count()
        if latest:
            url = reverse('admin:prescriptions_prescription_change', args=[latest.pk])
            return format_html(
                '<a href="{}">Prescription {} - {}</a>',
                url,
                latest.id,
                latest.issued_at.strftime("%Y-%m-%d"),
            )
        return "No prescriptions"
    get_latest_prescription.short_description = 'Latest Prescription'

    def create_prescription_button(self, obj):
        """Creates a prescription for that treatment plan and user"""
        button = format_html(
            '<a class="button" href="{}?user={}&appointment={}&treatment_plan={}">Create Prescription</a>',
            reverse('admin:prescriptions_prescription_add'),
            obj.user.pk,
            obj.initial_appointment.pk if obj.initial_appointment else '',
            obj.pk
        )
        return button
    create_prescription_button.short_description = 'Create Prescription'


@admin.register(TreatmentSession)
class TreatmentSessionAdmin(ModelAdmin):
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
class AppointmentRequestAdmin(ModelAdmin):
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