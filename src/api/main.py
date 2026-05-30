"""
CRM Digital — FastAPI application.

Endpoints:
  POST /webhooks/gmail        ← Gmail Pub/Sub push
  POST /webhooks/whatsapp     ← Twilio WhatsApp webhook
  POST /webhooks/web-form     ← Next.js support form
  GET  /tickets               ← List tickets (internal dashboard)
  GET  /reports/daily         ← Trigger daily sentiment report
  GET  /health                ← Health check
"""

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.agent import run_agent
from src.api.reports import generate_daily_report
from src.channels.gmail import fetch_new_messages, parse_pubsub_webhook, send_reply as gmail_reply
from src.channels.whatsapp import parse_twilio_webhook, send_reply as wa_reply
from src.channels.web_form import WebFormSubmission, parse_web_form
from src.db.models import Customer, Ticket
from src.db.session import AsyncSessionLocal, get_db, init_db


# ── App lifecycle ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="CRM Digital — Customer Success FTE", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api")


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "agent": "alex", "model": "gemini-1.5-pro"}


# ── Gmail webhook ──────────────────────────────────────────────────────────────

@router.post("/webhooks/gmail")
async def gmail_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    notification = parse_pubsub_webhook(payload)
    if not notification:
        return {"ignored": True}

    messages = fetch_new_messages(
        notification["history_id"],
        notification["email_address"],
    )

    results = []
    for msg in messages:
        result = await run_agent(
            db=db,
            customer_email=msg["email"],
            customer_name=msg["name"],
            channel="email",
            message_body=msg["body"],
        )
        # Send reply via Gmail
        if result["reply"] and not result["escalated"]:
            gmail_reply(
                thread_id=msg["thread_id"],
                to=msg["email"],
                subject=msg["subject"],
                body=result["reply"],
            )
        results.append({"ticket_id": result["ticket_id"], "escalated": result["escalated"]})

    return {"processed": len(results), "results": results}


# ── WhatsApp webhook ───────────────────────────────────────────────────────────

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    msg = parse_twilio_webhook(dict(form))
    if not msg:
        return {"ignored": True}

    result = await run_agent(
        db=db,
        customer_email=msg["email"],
        customer_name=msg["name"],
        channel="whatsapp",
        message_body=msg["body"],
        phone=msg["phone"],
    )

    if result["reply"] and not result["escalated"]:
        wa_reply(to_number=msg["phone"], body=result["reply"])

    return {"ticket_id": result["ticket_id"], "escalated": result["escalated"]}


# ── Web form endpoint ──────────────────────────────────────────────────────────

@router.post("/webhooks/web-form")
async def web_form_submit(
    submission: WebFormSubmission,
    db: AsyncSession = Depends(get_db),
):
    msg = parse_web_form(submission)

    result = await run_agent(
        db=db,
        customer_email=msg["email"],
        customer_name=msg["name"],
        channel="web_form",
        message_body=msg["body"],
        company=msg.get("company", ""),
    )

    return {
        "ticket_id": result["ticket_id"],
        "reply": result["reply"],
        "escalated": result["escalated"],
    }


# ── Internal: list tickets ─────────────────────────────────────────────────────

@router.get("/tickets")
async def list_tickets(
    status: str = "",
    channel: str = "",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)
    if status:
        query = query.where(Ticket.status == status)
    if channel:
        query = query.where(Ticket.channel == channel)
    result = await db.execute(query)
    tickets = result.scalars().all()
    return {
        "tickets": [
            {
                "id": str(t.id),
                "subject": t.subject,
                "status": t.status,
                "channel": t.channel,
                "priority": t.priority,
                "sentiment": t.sentiment_score,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tickets
        ]
    }


# ── Customers ─────────────────────────────────────────────────────────────────

@router.get("/customers")
async def list_customers(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).order_by(Customer.created_at.desc()).limit(limit))
    customers = result.scalars().all()

    rows = []
    for c in customers:
        ticket_res = await db.execute(select(Ticket).where(Ticket.customer_id == c.id))
        tickets = ticket_res.scalars().all()
        open_count = sum(1 for t in tickets if t.status in ("open", "in_progress", "escalated"))
        last_ticket = max((t.created_at for t in tickets), default=None)
        rows.append({
            "id": str(c.id),
            "name": c.name or "Unknown",
            "email": c.email,
            "phone": c.phone,
            "company": c.company,
            "plan": c.plan or "free",
            "ticket_count": len(tickets),
            "open_tickets": open_count,
            "last_activity": last_ticket.isoformat() if last_ticket else c.created_at.isoformat() if c.created_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return {"customers": rows}


# ── Daily report ───────────────────────────────────────────────────────────────

@router.get("/reports/daily")
async def daily_report(db: AsyncSession = Depends(get_db)):
    report = await generate_daily_report(db)
    return report


app.include_router(router)
