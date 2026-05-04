"""
WhatsApp channel handler via Twilio.

Receives: Twilio webhook POST (form-encoded).
Sends:    Reply via Twilio WhatsApp API.

Setup:
  1. Create Twilio account, enable WhatsApp sandbox or Business API
  2. Set webhook URL to https://yourdomain.com/webhooks/whatsapp
  3. Set env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
"""

import os
from typing import Any

from twilio.rest import Client


def parse_twilio_webhook(form_data: dict[str, Any]) -> dict | None:
    """
    Parse a Twilio WhatsApp webhook into a normalised ticket dict.
    form_data is the POST body parsed as a dict (FastAPI Form fields).

    Returns None if message should be ignored (status updates, etc).
    """
    body = form_data.get("Body", "").strip()
    if not body:
        return None

    from_number = form_data.get("From", "")  # e.g. "whatsapp:+1234567890"
    profile_name = form_data.get("ProfileName", "")

    # Strip "whatsapp:" prefix
    phone = from_number.replace("whatsapp:", "")

    return {
        "channel": "whatsapp",
        "phone": phone,
        "name": profile_name,
        "email": f"{phone.lstrip('+')}@whatsapp.placeholder",  # placeholder email for DB
        "subject": f"WhatsApp inquiry from {profile_name or phone}",
        "body": body,
        "wa_message_sid": form_data.get("MessageSid", ""),
    }


def send_reply(to_number: str, body: str) -> None:
    """
    Send a WhatsApp message via Twilio.
    to_number should be the E.164 number (e.g. "+1234567890") without "whatsapp:" prefix.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    if not account_sid or not auth_token:
        raise EnvironmentError("Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.")

    client = Client(account_sid, auth_token)
    client.messages.create(
        from_=from_number,
        to=f"whatsapp:{to_number}",
        body=body,
    )
