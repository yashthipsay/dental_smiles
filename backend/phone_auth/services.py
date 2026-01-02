import random
import logging
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

logger = logging.getLogger(__name__)

# OTP expiry time in minutes
OTP_EXPIRY_MINUTES = 5

def generate_otp():
    """Generate a 6-digit numeric OTP."""
    return str(random.randint(100000, 999999))

def send_otp_via_twilio(phone_number, otp):
    """Send OTP via Twilio SMS service."""
    # TODO: Uncomment and configure when ready for production
    # from twilio.rest import Client
    # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    # message = client.messages.create(
    #     body=f"Your OTP is: {otp}. Valid for {OTP_EXPIRY_MINUTES} minutes.",
    #     from_=settings.TWILIO_PHONE_NUMBER,
    #     to=phone_number
    # )
    # return message.sid

    # For development: Log the OTP
    logger.info(f"OTP for {phone_number}: {otp}")
    print(f"OTP for {phone_number}: {otp}")
    return True

def is_otp_valid(phone_otp_instance):
    """Check if the OTP is still valid (not expired)"""
    if not phone_otp_instance.otp_created_at:
        return False
    
    expiry_time = phone_otp_instance.otp_created_at + timedelta(minutes = OTP_EXPIRY_MINUTES)
    return timezone.now() < expiry_time

