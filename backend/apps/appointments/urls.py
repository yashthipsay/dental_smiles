from rest_framework.routers import DefaultRouter
from .views import AppointmentRequestViewSet, AppointmentViewSet

app_name = 'appointments'

router = DefaultRouter()
# Include the query is_whatsapp to check if the request is coming from the whatsapp or application
router.register(r"requests", AppointmentRequestViewSet, basename="appointmentrequest")
router.register(r"", AppointmentViewSet, basename="appointment")

urlpatterns = router.urls