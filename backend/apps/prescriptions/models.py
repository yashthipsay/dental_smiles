from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Medicine(models.Model):
    name = models.CharField(max_length=255, unique=True)

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(
        'Prescription',
        related_name='items',
        on_delete=models.CASCADE
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE
    )
    morning = models.BooleanField(default=False)
    afternoon = models.BooleanField(default=False)
    evening = models.BooleanField(default=False)

    before_after_food = models.CharField(max_length=12, choices=[
        ('before', 'Before Food'),
        ('after', 'After Food'),
    ])

    duration_days = models.PositiveIntegerField()



class Prescription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions"
    )
    treatment_plan = models.ForeignKey(
        'appointments.TreatmentPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions"
    )
    doctor_name = models.CharField(max_length=255)
    notes = models.TextField()

    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f"Prescription for {self.user.first_name} {self.user.last_name}"
            