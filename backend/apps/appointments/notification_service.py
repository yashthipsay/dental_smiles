import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class AppointmentEvent:
    CREATED = "appointment.created"
    UPDATED = "appointment.updated"
    CANCELLED = "appointment.deleted"

class UserEvent:
    CREATED = "user.created"
    UPDATED = "user.created"
    DELETED = "user.deleted"

class TreatmentPlanEvent:
    CREATED = "treatment_plan.created"
    UPDATED = "treatment_plan.updated"
    COMPLETED = "treatment_plan.completed"
    CANCELLED = "treatment_plan.cancelled"

class TreatmentSessionEvent:
    CREATED = "treatment_session.created"
    UPDATED = "treatment_session_updated"
    COMPLETED = "treatment_session_completed"
    CANCELLED = "treatment_session_cancelled"


def send_notification_on_whatsapp(instance, **kwargs):
    """
    Send WhatsApp notification to user about treatment session.
    Currently returns a mock response.
    TODO: Integrate with WhatsApp API (Twilio or similar)
    """
    event = kwargs.get('event')
    user = getattr(instance, 'user', None)
    if not user and hasattr(instance, 'treatment_plan'):
        user = instance.treatment_plan.user

    if not user:
        return {'status': 'failed', 'reason': 'No user associated with instance'}
    
    phone_number = user.phone_number
    full_name = f"{user.first_name} {user.last_name}".strip()
    message = ""

    if event == AppointmentEvent.CREATED:
        message = f"Hi {full_name}, your appointment at Blissful Smiles is confirmed for {instance.scheduled_at}. We look forward to seeing you!"
    elif event == TreatmentPlanEvent.CREATED:
        message = f"Hi {full_name}, a new {instance.get_treatment_type_display()} treatment plan has been prepared for you. We will help you through every step of your recovery."
    elif event == TreatmentSessionEvent.CREATED:
        message = f"Hi {full_name}, Session {instance.session_number} of your {instance.treatment_plan.get_treatment_type_display()} treatment is scheduled for {instance.scheduled_at}."
    else:
        return {'status': 'failed', 'reason': f'No whatsapp template for event: {event}'}
    
    logger.info(f"[WhatsApp] Sending to {phone_number}: {message}")

    return {
        'status': 'sent',
        'phone_number': phone_number,
        'user': full_name,
        'message': message.strip(),
        'timestamp': timezone.now().isoformat(),
    }

def send_notification_on_sms(instance, **kwargs):
    event = kwargs.get('event')
    user = getattr(instance, 'user', None)
    if not user and hasattr(instance, 'treatment_plaan'):
        user = instance.treatment_plan.user

    if not user:
        return {'status': 'failed', 'reason': 'No user associated with instance'}
    
    phone_number = user.phone_number
    full_name = f"{user.first_name} {user.last_name}".strip()
    message = ""

    if event == AppointmentEvent.UPDATED:
        message = f"Hi {full_name} your appointment at Blissful Smiles has been rescheduled to {instance.scheduled_at}."
    elif event == AppointmentEvent.CANCELLED:
        message = f"Hi {full_name}, your appointment for {instance.scheduled_at} has been cancelled."
    elif event == TreatmentPlanEvent.COMPLETED:
        message = f"Hi {full_name}, congratulations! Your {instance.get_treatment_type_display()} treatment plan is now complete."
    elif event == TreatmentSessionEvent.UPDATED:
        message = f"Hi {full_name}, Session {instance.session_number} of your treatment has been rescheduled to {instance.scheduled_at}."
    else:
        return {'status': 'failed', 'reason': f'No SMS template for event: {event}'}

    # Mock SMS send (for now, just log)
    logger.info(f"[SMS] Sending to {phone_number}: {message}")

    return {
        'status': 'sent',
        'phone_number': phone_number,
        'user': full_name,
        'message': message.strip(),
        'timestamp': timezone.now().isoformat(),
    }