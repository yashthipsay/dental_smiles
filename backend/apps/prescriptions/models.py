from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Prescription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    doctor_name = models.CharField(max_length=255)
    notes = models.TextField()

    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f"Prescription for {self.user.full_name}"
            