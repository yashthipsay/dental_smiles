from rest_framework.throttling import SimpleRateThrottle

class WhatsAppPrescriptionThrottle(SimpleRateThrottle):
    scope = "whatsapp_prescription"

    def get_cache_key(self, request, view):
        source = request.query_params.get("source")

        if source != "whatsapp":
            return None
        
        phone_number = request.query_params.get("phone_number")

        if not phone_number:
            return None
        
        return f"whatsapp-prescription:{phone_number}"