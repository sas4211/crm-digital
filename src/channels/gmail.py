"""
Gmail channel handler.

Receives: Gmail Pub/Sub push webhook (base64-encoded message data).
Sends:    Reply via Gmail API (creates a draft and sends it in the same thread).

Setup:
  1. Enable Gmail API in Google Cloud Console
  2. Create a Pub/Sub topic + subscription pointing to /webhooks/gmail
  3. Grant gmail.send + gmail.modify scopes to your service account
  4. Set GMAIL_CREDENTIALS_JSON env var (service account JSON)
"""

import base64
import json
import os
from email.mime.text import MIMEText

from google.oauth2 import service_account
from googleapiclient.discovery import build


def _gmail_service():
    creds_json = os.environ.get("GMAIL_CREDENTIALS_JSON")
    if not creds_json:
        raise EnvironmentError("Set GMAIL_CREDENTIALS_JSON env var.")
    info = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    ).with_subject(os.environ["GMAIL_USER"])
    return build("gmail", "v1", credentials=creds)


def parse_pubsub_webhook(payload: dict) -> dict | None:
    """
    Decode a Gmail Pub/Sub push message into a normalised ticket dict.
    Returns None if the message should be ignored (sent by us, no body, etc).

    Expected payload shape:
      {"message": {"data": "<base64>", "messageId": "..."}, "subscription": "..."}
    """
    try:
        data_b64 = payload["message"]["data"]
        data = json.loads(base64.b64decode(data_b64).decode())
        # data contains {"emailAddress": "...", "historyId": "..."}
        return {
            "history_id": data.get("historyId"),
            "email_address": data.get("emailAddress"),
        }
    except (KeyError, ValueError):
        return None


def fetch_new_messages(history_id: str, user_email: str) -> list[dict]:
    """
    Use the Gmail history API to fetch new messages since history_id.
    Returns a list of normalised message dicts.
    """
    svc = _gmail_service()
    history = (
        svc.users()
        .history()
        .list(userId="me", startHistoryId=history_id, historyTypes=["messageAdded"])
        .execute()
    )

    messages = []
    for record in history.get("history", []):
        for added in record.get("messagesAdded", []):
            msg_id = added["message"]["id"]
            msg = svc.users().messages().get(userId="me", id=msg_id, format="full").execute()
            parsed = _parse_gmail_message(msg)
            if parsed:
                messages.append(parsed)

    return messages


def _parse_gmail_message(msg: dict) -> dict | None:
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    sender = headers.get("from", "")
    subject = headers.get("subject", "(no subject)")
    thread_id = msg.get("threadId", "")

    # Extract plain-text body
    body = _extract_body(msg["payload"])
    if not body:
        return None

    # Parse email from "Name <email@domain.com>" format
    email = sender.split("<")[-1].strip(">") if "<" in sender else sender.strip()
    name = sender.split("<")[0].strip().strip('"') if "<" in sender else ""

    return {
        "channel": "email",
        "email": email,
        "name": name,
        "subject": subject,
        "body": body,
        "thread_id": thread_id,
        "message_id": msg["id"],
    }


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text from a Gmail message payload."""
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result
    return ""


def send_reply(thread_id: str, to: str, subject: str, body: str) -> None:
    """Send a reply email in the same Gmail thread."""
    svc = _gmail_service()
    mime = MIMEText(body)
    mime["to"] = to
    mime["subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
    mime["threadId"] = thread_id

    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    svc.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": thread_id},
    ).execute()
