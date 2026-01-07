from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TreatmentSession
from .notification_service import send_treatment_session_notification

@receiver(post_save, sender=TreatmentSession)
def auto_notify_treatment_session(sender, instance, created, **kwargs):
    """Automatically send WhatsApp notification when treatment session is created"""
    if created:
        response = send_treatment_session_notification(instance)
        instance.notification_sent = True
        instance.notified_at = timezone.now()
        instance.save(update_fields=['notification_sent', 'notified_at'])