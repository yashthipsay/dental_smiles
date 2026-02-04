from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from .throttles import WhatsAppPrescriptionThrottle

from .serializers import PrescriptionSerializer
from ..appointments.models import Appointment
from .models import Prescription
from .services.send import send_pdf_on_whatsapp 
from .services.pdf import generate_prescription_pdf
User = get_user_model()

class Prescriptions(APIView):
    # throttle_classes = [WhatsAppPrescriptionThrottle]
    def get_permissions(self):
        source = self.request.query_params.get('source')

        if source == "whatsapp":
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def post(self, request):
        phone_number = request.query_params.get("phone_number")

        if phone_number:
            phone_number = phone_number.replace(" ", "+")

        user = User.objects.filter(phone_number=phone_number).first()
        if not user:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        prescription = (
            Prescription.objects
            .filter(user=user)
            .order_by("-issued_at")
            .first()
        )

        if not prescription:
            return Response(
                {"error": "No prescription found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        success, message = send_pdf_on_whatsapp(prescription)

        if not success:
            return Response(
                {"error": message},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        
        return Response(
            {"message": "Prescription sent successfully"},
            status=status.HTTP_200_OK,
        )

class PrescriptionExists(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        phone_number = request.query_params.get("phone_number")

        if not phone_number:
            return Response(
                {"error": "Phone Number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        user_exists = User.objects.filter(phone_number=phone_number).exists()
        if not user_exists:
            return Response(
                {"error": "User does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        exists = Prescription.objects.filter(
            user__phone_number=phone_number
        ).exists()

        if exists:
            return Response({"exists": True})
        else:
            return Response({"exists": False}, status=status.HTTP_404_NOT_FOUND)

class PrescriptionPDFView(APIView):
    def get_permissions(self):
        source = self.request.query_params.get('source')

        if source == "whatsapp":
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get(self, request, *args, **kwargs):
        phone_number = request.query_params.get('phone_number')

        if not phone_number:
            return Response(
                {"error": "Phone number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        phone_number = phone_number.replace(" ", "+")  # Fixed typo: replacce -> replace

        user = User.objects.filter(phone_number=phone_number).first()

        if not user:
            return Response({
                "error": "User does not exist"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        prescription = (
            Prescription.objects
            .filter(user=user)
            .order_by("-issued_at")
            .first()
        )

        if not prescription:
            return Response(
                {"error": "No prescription found"},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            pdf = generate_prescription_pdf(prescription)

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename="prescription_{prescription.id}.pdf"'
            )
            response.write(pdf)
            return response  # Added missing return statement

        except Exception as e:
            return Response(
                {"error": f"Failed to generate PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # def get(self, request, *args, **kwargs):
    #     phone_number = request.query_params.get('phone_number')
    #     source = request.query_params.get("source")  



    #     user = User.objects.filter(phone_number=phone_number).first()

    #     if not user:
    #         Response({
    #             "error": "User does not exist"
    #         }, status=status.HTTP_400_BAD_REQUEST)

    #     appointments = Appointment.objects.filter(user = user)

    #     if not appointments.exists:
    #         return Response({"error": "Please book an appointment first"}, status = status.HTTP_400_BAD_REQUEST)

    #     latest_prescription = Prescription.objects.filter(user=User).first()

    #     if not latest_prescription:
    #         return Response({"error": "No prescriptions found for you!"}, status = status.HTTP_400_BAD_REQUEST)
        
    #     serializer = PrescriptionSerializer(latest_prescription)

    #     return Response(
    #         {
    #             "source": source,
    #             "phone_number": phone_number,
    #             "prescriptions": serializer.data
    #         }
    #     )



