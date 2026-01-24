from datetime import timedelta, timezone
from rest_framework import serializers
from .models import Appointment, AppointmentRequest, TreatmentPlan, TreatmentSession

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
    
    class TreatmentPlanSerializer(serializers.ModelSerializer):
        class Meta:
            model = TreatmentPlan
            fields = ['id',
                      'user',
                      'user_name',
                      'treatment_type',
                      'initial_appointment',
                      'total_amount',
                      'amount_paid',
                      'amount_remaining',
                      'estimated_duration_months',
                      'is_completed',
                      'created_at',
                      'updated_at',
                       ]
            read_only_fields = ['id', 'user_name', 'amount_remaining', 'created_at', 'updated_at']

        def get_user_name(self, obj):
            if obj.user:
                return f"{obj.user.first_name} {obj.user.last_name}".strip()
            return 'N/A'
        
        def validate(self, attrs):
            user = attrs.get('user')    
            appointment_user = attrs.get('initial_appointment').user if attrs.get('initial_appointment') else None
            if user and appointment_user and user != appointment_user:
                raise serializers.ValidationError("The user of the treatment plan must match the user of the related initial appointment.")
        
    class TreatmentSessionSerializer(serializers.ModelSerializer):
        class Meta:
            model = TreatmentSession
            fields = [
                'id',
                'treatment_plan',
                'user_name',
                'treatment_type',
                'session_number',
                'description',
                'amount_for_session',
                'amount_received',
                'scheduled_at',
                'completed_at',
                'notification_sent',
                'notified_at',
                'created_at',
                'updated_at',

            ]

            read_only_fields = [
                'id', 
                'user_name', 
                'treatment_type',
                'session_number', 
                'notification_sent', 
                'notified_at', 
                'created_at', 
                'updated_at'
            ]

        def get_user_name(self, obj):
            if obj.treatment_plan and obj.treatment_plan.user:
                return f"{obj.treatment_plan.user.first_name} {obj.treatment_plan.user.last_name}".strip()
            return 'N/A'

        def validate_scheduled_at(self, value):
            if value and value < timezone.now():
                raise serializers.ValidationError("Scheduled time cannot be in the past.")
            return value