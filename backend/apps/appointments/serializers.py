from datetime import timedelta, timezone
from rest_framework import serializers
from .models import Appointment, AppointmentRequest

class AppointmentSerializer(serializers.ModelSerializer):
    user_payment_method = serializers.CharField(source='user.payment_method')
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    scheduled_at = serializers.DateTimeField()


    class Meta:
        model = Appointment
        fields = ["id", "user_name", "scheduled_at", "status", "notes", "user_payment_method", "created_at"]
        read_only_fields = ["id", "user_name", "created_at"]

    def get_user_payment_method(self, obj):
        if obj.user.payment_method:
            return f"Paid using {obj.user.payment_method}"
        
    def validate_scheduled_at(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Scheduled time cannot be in the past.")

        

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

    def validate(self, attrs):
        scheduled_at = attrs.get('day_availability')
        if scheduled_at:
            end_time = scheduled_at + timedelta(minutes = 30)

            qs = Appointment.objects.filter(
                scheduled_at__lt=end_time,
                end_time__gt=scheduled_at
            )

            # Exclude self in case of update
            if self.instance:
                qs = qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError("The appointment time overlaps with an existing appointment. Choose a different time.")
        return attrs
    
    def validate_phone_number(self, value):
        if not value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Invalid phone number format")
        return value
    
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return 'N/A'
