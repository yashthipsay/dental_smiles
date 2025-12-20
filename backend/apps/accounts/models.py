from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email=email)

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

    objects = UserManager()

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