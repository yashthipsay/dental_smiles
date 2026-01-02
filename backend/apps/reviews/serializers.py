from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Review
        fields = ["id", "rating", "comment", "user_name", "created_at"]
        read_only_fields = ["id", "user_name", "created_at"]