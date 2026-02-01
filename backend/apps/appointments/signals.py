from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TreatmentSession, TreatmentPlan, Appointment
from .notification_service import send_notification_on_whatsapp
from .notification_service import (
        AppointmentEvent, TreatmentPlanEvent, TreatmentSessionEvent
    )

# 
@receiver(post_save, sender=TreatmentSession)
@receiver(post_save, sender=TreatmentPlan)
@receiver(post_save, sender=Appointment)
def auto_notify_treatment_session(sender, instance, created, **kwargs):
    """Automatically send WhatsApp notification when treatment session is created"""

    if sender == Appointment:
        if created: 
            send_notification_on_whatsapp(instance, event=AppointmentEvent.CREATED)
        else:
            event = AppointmentEvent.CANCELLED if instance.status == 'cancelled' else AppointmentEvent.UPDATED
            send_notification_on_whatsapp(instance, event=event)

    elif sender == TreatmentPlan:
        if created:
            send_notification_on_whatsapp(instance, event=TreatmentPlanEvent.CREATED)
        elif instance.is_completed:
            send_notification_on_whatsapp(instance, event=TreatmentPlanEvent.COMPLETED)
        else:
            send_notification_on_whatsapp(instance, event=TreatmentPlanEvent.UPDATED)

    elif sender == TreatmentSession:
        if created:
            send_notification_on_whatsapp(instance, event=TreatmentSessionEvent.CREATED)
        else:
            send_notification_on_whatsapp(instance, event=TreatmentSessionEvent.UPDATED)

    if hasattr(instance, 'notified_at'):
        sender.objects.filter(pk = instance.pk).update(notified_at=timezone.now())

    if created and hasattr(instance, 'notified_at'):
        sender.objects.filter(pk=instance.pk).update(notification_sent=True)

    # if created:
    #     response = send_treatment_session_notification(instance)
    #     instance.notification_sent = True
    #     instance.notified_at = timezone.now()
    #     instance.save(update_fields=['notification_sent', 'notified_at'])


