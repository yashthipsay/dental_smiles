from rest_framework.response import Response
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
    
"""
List of methods inside ModelViewSet:
 get -> list() -> QuerySet -> List View
 get -> retrieve() -> Product instance detail view
 post -> create -> new instance
 put -> Update
 pach -> Partial Update
 delete -> destroy -> delete instance
"""


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
    print("AppointmentRequestViewSet called")
    serializer_class = AppointmentRequestSerializer
    queryset = AppointmentRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        source = self.request.query_params.get("source", "").lower()
        if self.request.method == "POST" and source == "whatsapp":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]
    
    def create(self, request, *args, **kwargs):
        source = request.query_params.get("source", "").lower()
        if source =="whatsapp":
            phone_number = request.data.get("phone_number")
            if not phone_number:
                return Response(
                    {"error": "Phone number is required for WhatsApp requests."},
                    status=400,
                )
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user, _ = User.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    "first_name": "User",
                    "last_name": phone_number,
                },
            )
            serializer.save(user=user, source="whatsapp")
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)
        return super().create(request, *args, **kwargs)

