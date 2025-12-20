from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)

    age= models.PositiveSmallIntegerField()
    birth_date = models.DateField(null=True, blank=True)

    is_student = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'age']

    def __str__(self):
        return self.email
    
    class StudentProfile(models.Model):
        user = models.OneToOneField(
            "User",
            on_delete=models.CASCADE,
            related_name="student_profile"
        )

        college_name = models.CharField(max_length=255)
        student_id = models.CharField(max_length=100, unique=True)

        verified = models.BooleanField(default=False)
        verified_at = models.DateTimeField(null=True, blank=True)