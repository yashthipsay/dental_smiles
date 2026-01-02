import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class PhoneOTP(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='phone_profile',
        null=True, 
        blank=True
    )
    phone_number = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=100, null=True, blank=True)
    uid = models.CharField(max_length = 200, default=uuid.uuid4, unique=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} - {'Verified' if self.is_verified else 'Not Verified'}"
