import os
from fastapi import FastAPI, Form, Response, Request
from twilio.rest import Client
from redis import Redis
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Response, HTTPException
import httpx

load_dotenv()

app = FastAPI()

T1_STANDARD_SID = "***REMOVED***"
T2_PRESCRIPTION_SID = "***REMOVED***"
DJANGO_BACKEND_URL = "http://localhost:8000/api"
TWILIO_PHONE_NUMBER = "+14155238886"
FASTAPI_DOMAIN = "https://***REMOVED***.dev"

redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)
client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH"))

def check_prescription(patient_id: str):
    return True

@app.get("/fetch-prescription/{rx_id}")
async def fetch_prescription(rx_id: str, patient_id: str):
    clean_phone = patient_id.replace("whatsapp:", "")
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            f"{DJANGO_BACKEND_URL}/prescriptions/send_pdf/?source=whatsapp&phone_number={clean_phone}"
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
        rx_data = check_prescription(patient_id)
        target_sid = T2_PRESCRIPTION_SID if rx_data else T1_STANDARD_SID

        client.messages.create(
            from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
            to=patient_id,
            content_sid=target_sid
        )
        if rx_data:
            redis_client.setex(f"rx_id:{patient_id}", 3600, patient_id)
        
        redis_client.setex(f"session:{patient_id}", 3600, "MAIN_MENU")

    elif state == "MAIN_MENU":
        print("In MAIN_MENU state...")
        if message == "show_last": 
            rx_id = redis_client.get(f"rx_id:{patient_id}")
            pdf_url = f"{FASTAPI_DOMAIN}/fetch-prescription/{rx_id}?patient_id={patient_id}"

            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="Here is your latest prescription.",
                media_url=[pdf_url]
            )
        
        elif message == "ask a query":
            client.messages.create(
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=patient_id,
                body="Please type your query and we will get back to you shortly."
            )
            redis_client.setex(f"session:{patient_id}", 3600, "AWAITING_QUERY")
        
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