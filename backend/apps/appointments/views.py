from requests import Response
from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from .models import Appointment, AppointmentRequest
from .serializers import AppointmentRequestSerializer, AppointmentSerializer
from rest_framework.permissions import AllowAny

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

class AppointmentRequestViewSet(viewsets.ModelViewSet):

    serializer_class = AppointmentRequestSerializer
    queryset = AppointmentRequest.objects.all()
    
    def get_permissions(self):
        source = self.request.query_params.get("source")
        if source and source.lower() == "whatsapp":
            return [AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        source = request.query_params.get("source")
        if source and source and source.lower() == "whatsapp":
            phone_number = request.data.get("phone_number")
            if not phone_number:
                return Response(
                    {'error': 'Phone number is required for WhatsApp requests.'},
                    status=400
                )
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Get or create user with phone_number
            user, created = User.objects.get_or_create(
                phone_number=phone_number,
                defaults={'full_name': f'User {phone_number}'}  # Default name, admin can edit later
            )
            serializer.validated_data['user'] = user
            serializer.validated_data['source'] = source.lower()
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)
        else:
            pass

    def perform_create(self, serializer):
        serializer.save()
