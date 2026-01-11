from rest_framework import serializers
from .models import Appointment, AppointmentRequest

class AppointmentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ["id", "user_name", "scheduled_at", "status", "notes", "created_at"]
        read_only_fields = ["id", "user_name", "created_at"]

class AppointmentRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    
    class Meta:
        model = AppointmentRequest
        fields = [
            "id", 
            "user_name",
            "user_phone",
            "day_availability", 
            "phone_number", 
            "status", 
            "source", 
            "additional_notes", 
            "created_at"
        ]
        read_only_fields = ["id", "user_name", "user_phone", "created_at", "status", "source"]

    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return 'N/A'
