import logging
from django.utils import timezone

logger = logger.getLogger(__name__)

def send_treatment_session_notification(treatment_session):
    """
    Send WhatsApp notification to user about treatment session.
    Currently returns a mock response.
    TODO: Integrate with WhatsApp API (Twilio or similar)
    """
    user = treatment_session.treatment_plan.user
    phone_number = user.phone_number

    message = f"""
    Hi {user.full_name},

    A new treatment session has been scheduled for you.

    Treatment: {treatment_session.treatment_plan.get_treatment_type_display()}
    Session: {treatment_session.session_number}
    Scheduled: {treatment_session.scheduled_at}

    Please confirm your attendance.

    Thank you!
    """

    # Mock WhatsApp send (for now, just log)
    logger.info(f"Sending WhatsApp notification to {phone_number}")
    logger.info(f"Message content: {message}")

    return {
        'status': 'sent',
        'phone_number': phone_number,
        'user': user.full_name,
        'session_id': treatment_session.id,
        'message': message.strip(),
        'timestamp': timezone.now().isoformat(),
    }