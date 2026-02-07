import json
import os
from fastapi import FastAPI, Form, Response, Request
from twilio.rest import Client
from redis import Redis
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Response, HTTPException
import httpx

load_dotenv()

app = FastAPI()

T1_STANDARD_SID = os.getenv("T1_STANDARD_SID")
T2_PRESCRIPTION_SID = os.getenv("T2_PRESCRIPTION_SID")
T2_EXISTING_USER_SID = os.getenv("T2_EXISTING_USER_SID")
T3_MORE_OPTIONS_SID = os.getenv("T3_MORE_OPTIONS_SID")

# Backend and Twilio config
DJANGO_BACKEND_URL = os.getenv("DJANGO_BACKEND_URL", "http://localhost:8000/api")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
FASTAPI_DOMAIN = os.getenv("FASTAPI_DOMAIN")

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


@app.post("/twilio/status")
async def twilio_status(request: Request):
    """
    Twilio will POST message status updates here if status_callback is set.
    Useful to debug why a Content SID didn't render/deliver.
    """
    form = await request.form()
    # Twilio sends fields like: MessageSid, MessageStatus, ErrorCode, ErrorMessage (varies by channel)
    print("TWILIO STATUS:", dict(form))
    return Response(status_code=200)

async def check_prescription(patient_id: str):
    """Check if user has a prescription"""
    # Clean phone: whatsapp:+1234567890 -> +1234567890
    clean_phone = patient_id.replace("whatsapp:", "").strip()
    
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{DJANGO_BACKEND_URL}/prescriptions/exists/?source=whatsapp&phone_number={clean_phone}"
            )
            if response.status_code == 200:
                data = response.json()
                print(f"Prescription exists response: {data}")
                return data.get("exists", False)
            return False
    except Exception as e:
        print(f"Error checking prescription: {e}")
        return False

@app.get("/fetch-prescription/{rx_id}")
async def fetch_prescription(rx_id: str, patient_id: str):
    clean_phone = patient_id.replace("whatsapp:", "")
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            f"{DJANGO_BACKEND_URL}/prescriptions/send_pdf/",
            params={"source": "whatsapp", "phone_number": clean_phone}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        return Response(
            content=response.content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=prescription_{rx_id}.pdf"}
        )

@app.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(None),
    ButtonText: str = Form(None),
    ButtonPayload: str = Form(None),
):
    patient_id = From
    message = (
    ButtonPayload
    or ButtonText
    or Body
    or ""
).strip().lower()

    state = redis_client.get(f"session:{patient_id}") or "START"

    if message in ["hi", "hello", "menu"]:
        redis_client.setex(f"session:{patient_id}", 3600, "START")
        state = "START"
        print("MESSAGE:", message)
        print("STATE BEFORE:", state)

    if state == "START":
        print("Starting session...")
        try:
            has_prescription = await check_prescription(patient_id)
        except Exception as e:
            print(f"Error checking prescription: {e}")
            has_prescription = False
        
        # Show existing user menu if they have a prescription, otherwise general menu
        target_sid = T2_EXISTING_USER_SID if has_prescription else T1_STANDARD_SID

        client.messages.create(
            from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
            to=patient_id,
            content_sid=target_sid
        )
        if has_prescription:
            # Store clean phone number, not the full patient_id with "whatsapp:" prefix
            clean_phone = patient_id.replace("whatsapp:", "").strip()
            redis_client.setex(f"rx_id:{patient_id}", 3600, clean_phone)
        
        redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")

    elif state == "MAIN_MENU":
        print("In MAIN_MENU state...")
        if message == "show_last": 
            rx_id = redis_client.get(f"rx_id:{patient_id}")
            if not rx_id:
                client.messages.create(
                    from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                    to=patient_id,
                    body="❌ Could not retrieve prescription. Please try again."
                )
                redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")
                return Response(status_code=200)
            
            # rx_id is now just the phone number: +919175668567
            pdf_url = f"{FASTAPI_DOMAIN}/fetch-prescription/{rx_id}?patient_id={patient_id}"

            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="Here is your latest prescription.",
                media_url=[pdf_url]
            )
            redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")
        
        elif message == "btn_query":
            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="Looks like you have a query. We will get back to you shortly."
            )
            redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")
        
        elif message == "btn_book":
            print("Booking appointment...")
            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="Additional Notes (optional): Please provide any additional notes for your appointment."
            )
            redis_client.setex(f"session:{patient_id}", 3600, "AWAITING_APPOINTMENT_NOTES")

        elif message == "btn_more":
            print("Showing more options...")
            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                content_sid=T3_MORE_OPTIONS_SID,
                content_variables=json.dumps({}),
                status_callback=f"{FASTAPI_DOMAIN}/twilio/status"
            )
            redis_client.setex(f"session:{patient_id}", 3600, "MORE_MENU")

    elif state == "MORE_MENU":
        print("IN MORE MENU state...")
        if message == "btn_query":
            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="Looks like you have a query. We will get back to you shortly."
            )
            redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")

        elif message == "btn_treatments":
            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="🦷 *Our Treatment Plans*\n\n"
                     "• 🦴 Braces - Straighten your smile\n"
                     "• 👻 Invisalign - Invisible aligners\n"
                     "• 🌳 Root Canal - Save your tooth\n"
                     "• 💎 Implants - Replace missing teeth\n"
                     "• ✨ Teeth Whitening - Brighten your smile\n\n"
                    f"Our dental team would love to discuss this with you in detail.\n\n"
                    f"Would you like to 📅 book a consultation appointment?"
            )
            redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")

        elif message == "btn_about":
            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="ℹ️ *About Blissful Smiles*\n\n"
                     "🏥 *Excellence in Dental Care*\n\n"
                     "📍 123 FC Road, Deccan, Pune, Maharashtra 411005\n"
                     "📞 +91 12345 67890\n"
                     "🕐 Open: Mon-Sat, 9AM-6PM\n\n"
                     "We provide comprehensive dental services with the latest technology and compassionate care. "
                     "Your smile is our priority! 😊"
            )
            redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")

        if message == "show_last": 
            rx_id = redis_client.get(f"rx_id:{patient_id}")
            if not rx_id:
                client.messages.create(
                    from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                    to=patient_id,
                    body="❌ Could not retrieve prescription. Please try again."
                )
                redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")
                return Response(status_code=200)
            
            # rx_id is now just the phone number: +919175668567
            pdf_url = f"{FASTAPI_DOMAIN}/fetch-prescription/{rx_id}?patient_id={patient_id}"

            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="Here is your latest prescription.",
                media_url=[pdf_url]
            )
            redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")
        
        elif message == "btn_query":
            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="Looks like you have a query. We will get back to you shortly."
            )
            redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")
        
        elif message == "btn_book":
            print("Booking appointment...")
            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="Additional Notes (optional): Please provide any additional notes for your appointment."
            )
            redis_client.setex(f"session:{patient_id}", 3600, "AWAITING_APPOINTMENT_NOTES")

    elif state == "AWAITING_APPOINTMENT_NOTES":
        # Create appointment request
        appointment_date = redis_client.get(f"appointment_date:{patient_id}")
        additional_notes = message

        clean_phone = patient_id.replace("whatsapp:", "")
        
        async with httpx.AsyncClient() as http_client:
            print(f"Creating appointment for {clean_phone} on {appointment_date} with notes: {additional_notes}")
            payload = {
                "phone_number": clean_phone,
                "additional_notes": additional_notes,
            }
            
            try:
                response = await http_client.post(
                    f"{DJANGO_BACKEND_URL}/appointments/requests/?source=whatsapp",
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    client.messages.create(
                        from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                        to=patient_id,
                        body="✅ Your appointment request has been received! Our team will confirm your booking shortly.\n\nThank you for choosing us! 🦷"
                    )
                    redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")
                else:
                    client.messages.create(
                        from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                        to=patient_id,
                        body="❌ Failed to create appointment request. Please try again later."
                    )
                    redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")
            except Exception as e:
                client.messages.create(
                    from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                    to=patient_id,
                    body=f"❌ An error occurred. Please try again later. {e}"
                )
                redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")

    return Response(status_code=200)