import logging
from django.utils import timezone
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

class AppointmentEvent:
    CREATED = "appointment.created"
    UPDATED = "appointment.updated"
    COMPLETED = "appointment.completed"
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

def format_datetime(dt):
    return dt.strftime("%A, %d %b at %I:%M %p")

def send_notification_on_whatsapp(instance, **kwargs):
    """
    Send WhatsApp notification to user about treatment session.
    Currently returns a mock response.
    TODO: Integrate with WhatsApp API (Twilio or similar)
    """
    event = kwargs.get('event')
    print("Sending whatsapp message...")
    user = getattr(instance, 'user', None)
    if not user and hasattr(instance, 'treatment_plan'):
        user = instance.treatment_plan.user

    if not user:
        return {'status': 'failed', 'reason': 'No user associated with instance'}
    
    phone_number = user.phone_number
    full_name = f"{user.first_name} {user.last_name}".strip()
    message = ""

    if event == AppointmentEvent.CREATED:
        message = (
                f"Hi *{full_name}* 😊\n\n"
                f"Your appointment at *Blissful Smiles* is now confirmed! 🦷\n"
                f"📅 *{format_datetime(instance.scheduled_at)}*\n\n"
                f"We're looking forward to brightening your smile! ✨\n"
                f"See you soon!"
            )
    elif event == AppointmentEvent.UPDATED:
        message = (
            f"Hey *{full_name}* 👋\n\n"
            f"We've *updated* your appointment:\n"
            f"🆕 *{format_datetime(instance.scheduled_at)}*\n\n"
            f"Everything else stays the same. Questions? Just reply! 😄"
        )
    elif event == AppointmentEvent.COMPLETED:
        message = (
            f"Great seeing you today, *{full_name}*! 😁\n\n"
            f"Your appointment on *{format_datetime(instance.scheduled_at)}* is all wrapped up! 🎉\n\n"
            f"Keep up the great dental care - your smile looks fantastic! 🌟"
        )
    elif event == AppointmentEvent.CANCELLED:
        message = (
            f"Hi *{full_name}*,\n\n"
            f"Your appointment on *{format_datetime(instance.scheduled_at)}* has been cancelled 🗑️\n\n"
            f"Need to book a new one? We're here to help! 🌟 Reply anytime."
        )
    elif event == TreatmentPlanEvent.CREATED:
        message = (
                f"Hello *{full_name}* 🌟\n\n"
                f"Your new *{instance.get_treatment_type_display()}* treatment plan is ready! 🦷\n\n"
                f"We've planned everything to get you the best results — step by step.\n"
                f"Excited to start this journey with you! 🚀"
            )
    elif event == TreatmentPlanEvent.COMPLETED:
        message = (
            f"Wow *{full_name}* — you did it! 🎉\n\n"
            f"Your *{instance.get_treatment_type_display()}* treatment plan is officially *complete* 🏆\n\n"
            f"Your smile looks amazing — keep up the great work! 😁\n"
            f"We're so proud of you!"
        )
    elif event == TreatmentPlanEvent.CANCELLED:
        message = (
            f"Hi *{full_name}*,\n\n"
            f"Your *{instance.get_treatment_type_display()}* treatment plan has been cancelled.\n\n"
            f"No worries — whenever you're ready to continue, just let us know ❤️"
        )
    elif event == TreatmentSessionEvent.CREATED:
        message = (
                f"Hi *{full_name}* 😄\n\n"
                f"*Session {instance.session_number}* of your *{instance.treatment_plan.get_treatment_type_display()}* plan is scheduled!\n"
                f"📅 *{format_datetime(instance.scheduled_at)}*\n\n"
                f"Get ready for the next step toward a healthier smile! ✨"
            )
    elif event == TreatmentSessionEvent.UPDATED:
        message = (
            f"Hey *{full_name}*,\n\n"
            f"We've *rescheduled* Session {instance.session_number}:\n"
            f"🆕 *{format_datetime(instance.scheduled_at)}*\n\n"
            f"Sorry for any inconvenience — we'll make it worth it! 🦷😊"
        )

    elif event == TreatmentSessionEvent.COMPLETED:
        message = (
            f"Great job today, *{full_name}*! 👏\n\n"
            f"*Session {instance.session_number}* is successfully completed 🎯\n\n"
            f"You're making awesome progress — keep shining! 🌟"
        )

    elif event == TreatmentSessionEvent.CANCELLED:
        message = (
            f"Hi *{full_name}*,\n\n"
            f"Session {instance.session_number} has been cancelled.\n\n"
            f"Want to pick a new time? Just reply — we've got you! 😊"
        )
    else:
        return {'status': 'failed', 'reason': f'No whatsapp template for event: {event}'}
    
    logger.info(f"[WhatsApp] Sending to {phone_number}: {message}")

    client.messages.create(
        body=message,
        to=f"whatsapp:{phone_number}",
        from_=settings.TWILIO_WHATSAPP_NUMBER,
    )

    return {
        'status': 'sent',
        'phone_number': phone_number,
        'user': full_name,
        'message': message.strip(),
        'timestamp': timezone.now().isoformat(),
    }

# def send_notification_on_sms(instance, **kwargs):
#     event = kwargs.get('event')
#     user = getattr(instance, 'user', None)
#     if not user and hasattr(instance, 'treatment_plaan'):
#         user = instance.treatment_plan.user

#     if not user:
#         return {'status': 'failed', 'reason': 'No user associated with instance'}
    
#     phone_number = user.phone_number
#     full_name = f"{user.first_name} {user.last_name}".strip()
#     message = ""

#     if event == AppointmentEvent.UPDATED:
#         message = f"Hi {full_name} your appointment at Blissful Smiles has been rescheduled to {instance.scheduled_at}."
#     elif event == AppointmentEvent.CANCELLED:
#         message = f"Hi {full_name}, your appointment for {instance.scheduled_at} has been cancelled."
#     elif event == TreatmentPlanEvent.COMPLETED:
#         message = f"Hi {full_name}, congratulations! Your {instance.get_treatment_type_display()} treatment plan is now complete."
#     elif event == TreatmentSessionEvent.UPDATED:
#         message = f"Hi {full_name}, Session {instance.session_number} of your treatment has been rescheduled to {instance.scheduled_at}."
#     else:
#         return {'status': 'failed', 'reason': f'No SMS template for event: {event}'}

#     # Mock SMS send (for now, just log)
#     logger.info(f"[SMS] Sending to {phone_number}: {message}")

#     client.messages.create(
#         body=message,
#         to=f"{phone_number}",
#         from_=settings.TWILIO_PHONE_NUMBER,
#     )

#     return {
#         'status': 'sent',
#         'phone_number': phone_number,
#         'user': full_name,
#         'message': message.strip(),
#         'timestamp': timezone.now().isoformat(),
#     }