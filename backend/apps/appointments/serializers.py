from rest_framework import serializers
from .models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["id", "scheduled_at", "status", "created_at"]
        read_only_fields = ["id", "created_at"]