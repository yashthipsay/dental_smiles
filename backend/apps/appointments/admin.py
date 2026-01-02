from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from pytz import timezone
from .models import Appointment, TreatmentSession, TreatmentPlan
from .notification_service import send_treatment_session_notification

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'scheduled_at', 'status', 'created_at']
    list_filter = ['status', 'scheduled_at', 'created_at']
    search_fields = ['user__phone_number', 'user__full_name']
    readonly_fields = ['created_at']
    ordering = ['-scheduled_at']

@admin.register(TreatmentSession)
class TreatmentSessionAdmin(admin.ModelAdmin):
    list_display = ['get_user_name', 'get_treatment_type', 'session_number', 'scheduled_at', 'notification_status', 'notify_button']
    list_filter = ['treatment_plan__treatment_type', 'scheduled_at', 'notification_sent']
    search_fields = ['treatment_plan__user__phone_number', 'treatment_plan__user__full_name']
    readonly_fields = ['created_at', 'updated_at', 'notification_sent', 'notified_at']

    fieldsets = (
        ('Treatment Sessiono Info', {
            'fields': ('treatment_plan', 'appointment', 'session_number', 'description')
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
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_user_name(self, obj):
        return obj.treatment_plan.user.full_name
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
                '<a class="button" href="{}">Send WhatsApp</a>',
                reverse('admin:send-treatment-session-notification', args=[obj.pk])
            )
        return format_html('<span style="color: gray;">Already Sent</span>')
    notify_button.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:session_id>/notify/',
                self.admin_site.adamin_view(self.send_notification_action),
                name='send-treatment-session-notification'
            ),
        ]
        return custom_urls + urls
    
    def send_notification_action(self, request, session_id):
        """Custom admin action to send WhatsApp notification"""
        try:
            treatment_session = TreatmentSession.objects.get(pk=session_id)
            response = send_treatment_session_notification(treatment_session)

            # Update notification status
            treatment_session.notification_sent = True
            treatment_session.notified_at = timezone.now()
            treatment_session.save()

            self.message_user(
                request,
                f"WhatsApp ntification sent to {treatment_session.treatment_plan.user.full_name}."
            )
        except TreatmentSession.DoesNotExist:
            self.message_user(request, "Treatment session not found", level='error')

        return HttpResponseRedirect(
            reverse('admin:appointments_treatmentsession_changelist')
        )
            