from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Prescription
from django.conf import settings
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

# Use the same SID as in your WhatsApp client for prescription menus
T2_PRESCRIPTION_SID = "***REMOVED***"

@receiver(pre_save, sender=Prescription)
def store_original_values(sender, instance, **kwargs):
    """Store original field values to detect changes"""
    if instance.pk:
        try:
            instance._original = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._original = None
    else:
        instance._original = None


@receiver(post_save, sender=Prescription)
def notify_new_created_prescription(sender, instance, created, **kwargs):
    if created:
        try:
            user = instance.user
            
            client.messages.create(
                from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                to=f"whatsapp:{user.phone_number}",
                content_sid=T2_PRESCRIPTION_SID
            )
            logger.info(f"Prescription notfication sent to {user.phone_number}")

        except Exception as e:
            logger.error(f"Failed to send prescription notification: {str(e)}")

        