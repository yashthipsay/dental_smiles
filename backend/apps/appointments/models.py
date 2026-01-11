from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone
from .notification_service import send_treatment_session_notification

User = settings.AUTH_USER_MODEL

# This is just a normal appointment model for regular check-ups and consultations.
class Appointment(models.Model):
    """Base appointment model for regular check-ups and consultations."""
    APPOINTMENT_STATUS = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="appointments"
    )
    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=APPOINTMENT_STATUS,
        db_index=True
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['user', 'scheduled_at']),
        ]
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Appointment for {self.user.first_name} {self.user.last_name} on {self.scheduled_at}"

class AppointmentRequest(models.Model):
    """Appointment requests made by users"""
    REQUEST_STATUS = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("canceled", "Canceled")
    ]

    SOURCE = [
        ("whatsapp", "WhatsApp"),
        ("app", "App"),
    ]
    # nullable field
    day_availability = models.DateField(null=True, blank=True)   
    # Patient will not specify start time availability and end time availability. We will store it from the admin panel
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="appointment_requests"
    )
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    source = models.CharField(
        max_length=20,
        choices=SOURCE,
        default="app",
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=REQUEST_STATUS,
        default="pending",
        db_index=True)
    additional_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class FollowUp(models.Model):
    """Follow-up visits/notes for an appointment"""
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="follow_ups"
    )
    notes = models.TextField()
    scheduled_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Follow-up for {self.appointment} on {self.scheduled_at}"

class TreatmentPlan(models.Model):
    """Treatment plans associated with an appointment"""
    TREATMENT_TYPES = [
        ("braces", "Braces"),
        ("invisalign", "Invisalign"),
        ("root_canal", "Root Canal"),
        ("implant", "Implant"),
        ("whitening", "Whitening"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="treatment_plans"
    )

    treatment_type = models.CharField(
        max_length=50,
        choices=TREATMENT_TYPES,
        db_index=True
    )
    initial_appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="treatment_plans"
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    estimated_duration_months = models.IntegerField()
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def amount_remaining(self):
        """Calculate remaining amount dynamically"""
        return self.total_amount - self.amount_paid
    
    def __str__(self):
        return f"{self.treatment_type} plan for {self.user.first_name} {self.user.last_name}"
    
class TreatmentSession(models.Model):
    """Individual sessions/phases of a treatment plan"""
    treatment_plan = models.ForeignKey(
        TreatmentPlan,
        on_delete=models.CASCADE,
        related_name="sessions"
    )
    
    session_number = models.PositiveIntegerField()
    description = models.TextField()
    amount_for_session = models.DecimalField(max_digits=10, decimal_places=2)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    notification_sent = models.BooleanField(default=False)
    notified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session_number']
        unique_together = ['treatment_plan', 'session_number']

    def save(self, *args, **kwargs):
        # Check if this is an existing session (update) or new session (create)
        if self.pk:
            # This is an update - get the old instance
            old_instance = TreatmentSession.objects.get(pk=self.pk)
            old_amount_received = old_instance.amount_received
            
            # Calculate the difference
            amount_difference = self.amount_received - old_amount_received
            
            # Update treatment plan amount paid with the difference
            self.treatment_plan.amount_paid += amount_difference
            self.treatment_plan.save()
        else:
            # This is a new session (create)
            if not self.session_number:
                last_session = TreatmentSession.objects.filter(
                    treatment_plan=self.treatment_plan
                ).order_by('-session_number').first()

                if last_session:
                    self.session_number = last_session.session_number + 1
                else:
                    self.session_number = 1

            if not self.amount_received:
                self.amount_received = 0
            
            # Add the new amount to treatment plan
            updated_amount = self.treatment_plan.amount_paid + self.amount_received
            self.treatment_plan.amount_paid = updated_amount
            self.treatment_plan.save()

        super().save(*args, **kwargs)
    

    def __str__(self):
        return f"Session {self.session_number} - {self.treatment_plan}"


class Prescription(models.Model):
    """Prescriptions linked to appointments"""
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions"
    )
    treatment_plan = models.ForeignKey(
        TreatmentPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions"
    )
    
    doctor_name = models.CharField(max_length=255)
    notes = models.TextField()
    medications = models.JSONField(default=list, blank=True)  # Store as list of dicts
    
    issued_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issued_at']




    def __str__(self):
        return f"Prescription for {self.appointment or self.treatment_plan}"
