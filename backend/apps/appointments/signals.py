from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TreatmentSession, TreatmentPlan, Appointment
from .notification_service import send_notification_on_whatsapp
from .notification_service import (
        AppointmentEvent, TreatmentPlanEvent, TreatmentSessionEvent
    )

@receiver(pre_save, sender=Appointment)
@receiver(pre_save, sender=TreatmentPlan)
@receiver(pre_save, sender=TreatmentSession)
def store_original_values(sender, instance, **kwargs):
    """Store original field values to detect changes"""
    if instance.pk:
        try:
            instance._original = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._original = None
    else:
        instance._original = None


# 
@receiver(post_save, sender=TreatmentSession)
@receiver(post_save, sender=TreatmentPlan)
@receiver(post_save, sender=Appointment)
def auto_notify_treatment_session(sender, instance, created, **kwargs):
    """Automatically send WhatsApp notification when treatment session is created"""
    
    should_notify = False
    event = None

    original = getattr(instance, '_original', None)
    if hasattr(instance, '_original'):
        delattr(instance, '_original')

        if sender == Appointment:
            if created:
                should_notify = True
                event = AppointmentEvent.CREATED
            else:

                if original:
                    if instance.status != original.status:
                        if instance.status == 'completed':
                            should_notify = True
                            event = AppointmentEvent.COMPLETED
                        elif instance.status == 'canceled':
                            should_notify = True
                            event = AppointmentEvent.CANCELLED
                    elif instance.scheduled_at != original.scheduled_at:
                        should_notify = True
                        event = AppointmentEvent.UPDATED

        elif sender == TreatmentPlan:
            if created:
                should_notify = True
                event = TreatmentPlanEvent.CREATED
            else:
                if original:
                    # Check if is_completed changed to True
                    if instance.is_completed and not original.is_completed:
                        should_notify = True
                        event = TreatmentPlanEvent.COMPLETED
                    # Check for other meaningful changes
                    elif not instance.is_completed and (
                        instance.treatment_type != original.treatment_type or
                        instance.status != original.status
                    ):
                        should_notify = True
                        event = TreatmentPlanEvent.UPDATED
        elif sender == TreatmentSession:
            if created:
                should_notify = True
                event = TreatmentSessionEvent.CREATED
            else:
                if original:
                    if instance.scheduled_at != original.scheduled_at:
                        should_notify = True
                        event = TreatmentSessionEvent.UPDATED

                    elif instance.status != original.status:
                        if instance.status == 'completed':
                            should_notify = True
                            event = TreatmentSessionEvent.COMPLETED
                        elif instance.status == 'cancelled':
                            should_notify = True
                            event = TreatmentSessionEvent.CANCELLED

        # Send notification only if there was a meaningful change
        if should_notify and event:
            send_notification_on_whatsapp(instance, event=event)
            
            # Update notification timestamp
            if hasattr(instance, 'notified_at'):
                sender.objects.filter(pk=instance.pk).update(
                    notified_at=timezone.now(),
                    notification_sent=True
                )


    # if created:
    #     response = send_treatment_session_notification(instance)
    #     instance.notification_sent = True
    #     instance.notified_at = timezone.now()
    #     instance.save(update_fields=['notification_sent', 'notified_at'])


