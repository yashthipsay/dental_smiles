from rest_framework import serializers
from .models import Appointment, AppointmentRequest

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["id", "scheduled_at", "status", "created_at"]
        read_only_fields = ["id", "created_at"]

# Take appointment requests and save them only if whatsapp is enabled right now, otherwise pass
class AppointmentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentRequest
        fields = ["id", "start_time_availibility", "end_time_availibility", "phone_number", "status", "source", "additional_notes", "created_at"]
        read_only_fields = ["id", "created_at", "status", "source"]
