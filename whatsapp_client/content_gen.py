import os
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict


TWILIO_CONTENT_URL = "https://content.twilio.com/v1/Content"

AUTH = HTTPBasicAuth(
    f"{os.getenv('TWILIO_ACCOUNT_SID')}",
    f"{os.getenv('TWILIO_AUTH_TOKEN')}",
)


def create_twilio_content(payload: Dict) -> Dict:
    """
    Creates a Twilio Content template and returns the API response.

    Raises:
        requests.HTTPError if the request fails
    """
    response = requests.post(
        TWILIO_CONTENT_URL,
        json=payload,
        auth=AUTH,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


GENERAL_MENU_V5 = {
    "friendly_name": "general_menu_v5",
    "language": "en",
    "types": {
        "twilio/quick-reply": {
            "body": (
                "👋 Welcome to Dental Smiles!\n\n"
                "How can we assist you today?"
            ),
            "actions": [
                {"title": "📅 Book Appointment", "id": "btn_book"},
                {"title": "❓ Ask a Query", "id": "btn_query"},
                {"title": "🦷 Treatment Plans", "id": "btn_treatments"},
            ],
        }
    },
}

PRESCRIPTION_MENU_V5 = {
    "friendly_name": "prescription_menu_v5",
    "language": "en",
    "types": {
        "twilio/quick-reply": {
            "body": (
                "📝 Your prescription is available.\n\n"
                "You can view it below or ask us if you have any questions."
            ),
            "actions": [
                {"title": "📄 View Prescription", "id": "show_last"},
                {"title": "❓ Ask a Question", "id": "btn_query"},
            ],
        }
    },
}

if __name__ == "__main__":
    from pprint import pprint

    general_menu = create_twilio_content(GENERAL_MENU_V5)
    prescription_menu = create_twilio_content(PRESCRIPTION_MENU_V5)

    print("✅ General Menu SID:", general_menu["sid"])
    print("✅ Prescription Menu SID:", prescription_menu["sid"])