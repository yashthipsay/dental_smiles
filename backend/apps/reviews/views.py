from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from .models import Review
from django.http import Http404
from .serializers import ReviewSerializer
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions

User = get_user_model()


class ReviewList(ListCreateAPIView):
    serializer_class = ReviewSerializer
    queryset = Review.objects.all()

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAdminUser()]
        
        if self.request.method == "POST":
            source = self.request.query_params.get("source")
            if source == "whatsapp":
                return [AllowAny()]
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        phone_number = self.request.query_params.get("phone_number")
        if phone_number:
            phone_number = phone_number.replace(" ", "+")
        user = User.objects.filter(phone_number=phone_number).first()
        serializer.save(user=user)

