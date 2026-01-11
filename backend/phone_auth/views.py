from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import PhoneOTP
from .serializers import SendOTPSerializer, VerifyOTPSerializer, PhoneOTPSerializer
from .services import generate_otp, send_otp_via_twilio, is_otp_valid

User = get_user_model()

class SendOTPView(APIView):
    """
    Send OTP to the user's phone number.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']

        otp = generate_otp()

        # Create or update PhoneOTP record based on phone_number
        phone_otp, created = PhoneOTP.objects.update_or_create(
            phone_number=phone_number,
            defaults={
                'otp': otp,
                'otp_created_at': timezone.now(),
                'is_verified': False,
            }   
        )

        # Send OTP (logs for now)
        send_otp_via_twilio(phone_number, otp)

        return Response({
            'message': 'OTP sent successfully',
            'uid': str(phone_otp.uid),
        }, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    """
    Verify OTP and Login/Register user
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        otp = serializer.validated_data['otp']
        full_name = serializer.validated_data.get('full_name')

        try:
            phone_otp = PhoneOTP.objects.get(phone_number=phone_number)
        except PhoneOTP.DoesNotExist:
             return Response({'error': 'Invalid phone number'}, status=404)

        # Check if OTP is expired
        if not is_otp_valid(phone_otp):
            return Response({
                'error': 'OTP has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify OTP
        if phone_otp.otp != otp:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Mark as verified and clear OTP
        phone_otp.is_verified = True
        phone_otp.otp = None
        phone_otp.save()

        # Get or Create User
        is_new_user = False
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            if not full_name:
                return Response({
                    'error': 'Full name is required for new user registration',
                    'is_new_user': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.create_user(phone_number=phone_number,
                                            first_name=full_name.split(" ")[0] if full_name else "User",
                                            last_name=" ".join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else phone_number
                                            )
            is_new_user = True

        # Link OTP profile to user if not linked
        if not phone_otp.user:
            phone_otp.user = user
            phone_otp.save()

        # Generate JWT Tokens
        refresh = RefreshToken.for_user(user)

        # Check if profile is complete
        profile_complete = is_profile_complete(user)

        return Response({
            'message': 'Login successful',
            'uid': str(phone_otp.uid),
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'is_new_user': is_new_user,
            'is_profile_complete': profile_complete,
            'user': {
                'id': user.id,
                'phone_number': user.phone_number,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'age': user.age,
                'birth_date': str(user.birth_date) if user.birth_date else None,
            }
        }, status=status.HTTP_200_OK)
    
class ResendOTPView(APIView):
    """
    Resend OTP to the user's phone number.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
             return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            phone_otp = PhoneOTP.objects.get(phone_number=phone_number)
        except PhoneOTP.DoesNotExist:
            return Response({
                'error': 'No OTP request found to resend'
            }, status=status.HTTP_404_NOT_FOUND)
    
        # Generate new OTP
        otp = generate_otp()

        phone_otp.otp = otp
        phone_otp.otp_created_at = timezone.now()
        phone_otp.is_verified = False
        phone_otp.save()

        # Send OTP (logs for now)
        send_otp_via_twilio(phone_otp.phone_number, otp)

        return Response({
            'message': 'OTP resent successfully',
            'uid': str(phone_otp.uid),
        }, status=status.HTTP_200_OK)
    

def is_profile_complete(user):
    """
    Check if user profile has all required fields filled.
    Required fields: full_name, email, age or birth_date
    """
    required_fields_filled = all([
        user.full_name,
        user.email,
        user.age is not None or user.birth_date is not None,
    ])
    return required_fields_filled


class IsAlreadyRegisteredView(APIView):
    """
    Check if a phone number is already registered in the system.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({
                'error': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user exists with this phone number
        user_exists = User.objects.filter(phone_number=phone_number).exists()

        return Response({
            'phone_number': phone_number,
            'is_registered': user_exists,
        }, status=status.HTTP_200_OK)
        

class IsProfileCompleteView(APIView):
    """
    Check if the authenticated user's profile is complete.
    Returns which fields are missing if incomplete.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        missing_fields = []

        if not user.full_name:
            missing_fields.append('full_name')
        if not user.email:
            missing_fields.append('email')
        if user.age is None and user.birth_date is None:
            missing_fields.append('age_or_birth_date')

        profile_complete = len(missing_fields) == 0

        return Response({
            'is_profile_complete': profile_complete,
            'missing_fields': missing_fields,
            'user': {
                'id': user.id,
                'phone_number': user.phone_number,
                'full_name': user.full_name,
                'email': user.email,
                'age': user.age,
                'birth_date': str(user.birth_date) if user.birth_date else None,
                'is_student': user.is_student,
            }
        }, status=status.HTTP_200_OK)
    
    
class PhoneStatusView(APIView):
    """
    Get the verification status of the user's phone number
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            phone_otp = PhoneOTP.objects.get(user=user)
            serializer = PhoneOTPSerializer(phone_otp)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PhoneOTP.DoesNotExist:
            return Response({
                'error': 'No phone number associated with this user'
            }, status=status.HTTP_404_NOT_FOUND)
