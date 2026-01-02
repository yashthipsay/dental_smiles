from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from .models import Review
from .serializers import ReviewSerializer

User = get_user_model()

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allow owners to manage their reviews ad admins to manage all.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True
        return obj.user == request.user

class ReviewViewSet(viewsets.ModelViewSet):
    """
    list: List all reviews
    create: Submit a new review
    retrieve: Get a specific review.
    update/partial_update: Modify your review (only yours unless admin).
    destroy: Delete your review (only yours unless admin).
    """

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return Review.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        

