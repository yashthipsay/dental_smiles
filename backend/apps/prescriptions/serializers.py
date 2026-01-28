from rest_framework import serializers
from .models import Prescription, PrescriptionItem, Medicine

class MedicineSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Medicine
        fields = ['id', 'name']

class PrescriptionItemSerializer(serializers.ModelSerializer):
    medicine = MedicineSerializer(read_only=True)
    medicine_id = serializers.PrimaryKeyRelatedField(
        queryset=Medicine.objects.all(),
        write_only=True,
        source = 'medicine'
    )

    class Meta:
        model = PrescriptionItem
        fields = [
            'id',
            'medicine',
            'medicine_id',
            'morning',
            'afternoon',
            'evening',
            'before_after_food',
            'duration_days'
        ]

class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    doctor_name = serializers.CharField(max_length=255)

    class Meta:
        model = Prescription
        fields = [
            'id',
            'user',
            'appointment',
            'treatment_plan',
            'doctor_name',
            'prescription_number',
            'notes',
            'issued_at',
            'items'
        ]
        read_only_fields = ['id', 'prescription_number', 'issued_at', 'user'] 
        

