from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Appointment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length = 20,
        choices=[
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("completed", "Completed"),
            ("canceled", "Canceled"),
        ],
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['scheduled_at']),
        ]
