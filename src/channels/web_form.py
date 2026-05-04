"""
Web Form channel handler.

Receives: JSON POST from the Next.js support form at /webhooks/web-form.
Sends:    Response JSON back to the form (displayed inline) + optional email.
"""

from pydantic import BaseModel, EmailStr


class WebFormSubmission(BaseModel):
    """Validated shape of the incoming web form POST body."""
    name: str
    email: EmailStr
    company: str = ""
    subject: str
    message: str
    priority: str = "medium"   # low | medium | high


def parse_web_form(data: WebFormSubmission) -> dict:
    """
    Convert a validated web form submission into the normalised ticket dict
    that the agent and channel router expect.
    """
    return {
        "channel": "web_form",
        "email": data.email,
        "name": data.name,
        "company": data.company,
        "subject": data.subject,
        "body": data.message,
        "priority": data.priority,
    }
