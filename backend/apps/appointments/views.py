from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from .models import Appointment
from .serializers import AppointmentSerializer

User = get_user_model()

class isOwnerOrAdmin(permissions.BasePermission):
    """
    Allow owners to manage theirr appointments and admins to manage all.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True
        return obj.user == request.user
    
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    list: List your appointments.
    create: Create a new appointment.
    retrieve: Get an appointment (only yours unless admin).
    update/partial_update: Modify an appointment (only yours unless admin).
    destroy: Delete an appointment (only yours unless admin).    list: List your appointments.
    create: Create a new appointment.
    retrieve: Get an appointment (only yours unless admin).
    update/partial_update: Modify an appointment (only yours unless admin).
    destroy: Delete an appointment (only yours unless admin).
    """
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, isOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Appointment.objects.all()
        return Appointment.objects.filter(user=user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

