"""
seed.py — populate the local SQLite DB with demo data.
Run:  python seed.py
"""

import asyncio
import uuid
from datetime import datetime, timedelta, date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import AsyncSessionLocal, init_db
from src.db.models import Customer, Ticket, DailyReport


# ── Demo customers ─────────────────────────────────────────────────────────────

CUSTOMERS = [
    {"email": "priya.sharma@novatech.io",    "name": "Priya Sharma",    "company": "NovaTech",      "plan": "pro"},
    {"email": "james.okafor@bridgeops.com",  "name": "James Okafor",   "company": "BridgeOps",     "plan": "starter"},
    {"email": "sofia.mendez@lunacreative.co","name": "Sofia Mendez",   "company": "Luna Creative",  "plan": "free"},
    {"email": "tom.wu@quantumleap.io",       "name": "Tom Wu",          "company": "Quantum Leap",  "plan": "enterprise"},
    {"email": "aisha.bell@stackflow.dev",    "name": "Aisha Bell",      "company": "StackFlow",     "plan": "pro"},
    {"email": "marcus.reid@cleargrid.com",   "name": "Marcus Reid",     "company": "ClearGrid",     "plan": "starter"},
    {"email": "elena.voss@pinnacleHR.de",    "name": "Elena Voss",      "company": "PinnacleHR",    "plan": "enterprise"},
    {"email": "dan.foster@looptask.io",      "name": "Dan Foster",      "company": "LoopTask",      "plan": "free"},
]


# ── Demo tickets ───────────────────────────────────────────────────────────────

def mins_ago(n): return datetime.utcnow() - timedelta(minutes=n)
def hrs_ago(n):  return datetime.utcnow() - timedelta(hours=n)

TICKETS = [
    # Open
    {"subject": "Can't log in after password reset",             "status": "open",             "channel": "web_form", "priority": "high",     "sentiment": -0.62, "customer_idx": 0, "created": mins_ago(8)},
    {"subject": "Invoice shows wrong VAT amount",                "status": "open",             "channel": "email",    "priority": "medium",   "sentiment": -0.31, "customer_idx": 5, "created": mins_ago(22)},
    {"subject": "How do I add a second workspace?",              "status": "open",             "channel": "web_form", "priority": "low",      "sentiment":  0.41, "customer_idx": 2, "created": mins_ago(45)},
    # In progress
    {"subject": "WhatsApp notifications not delivering",         "status": "in_progress",      "channel": "whatsapp", "priority": "high",     "sentiment": -0.48, "customer_idx": 4, "created": hrs_ago(1)},
    {"subject": "Zapier integration throwing 401 errors",        "status": "in_progress",      "channel": "email",    "priority": "high",     "sentiment": -0.55, "customer_idx": 1, "created": hrs_ago(2)},
    {"subject": "Export to CSV missing custom field columns",    "status": "in_progress",      "channel": "web_form", "priority": "medium",   "sentiment": -0.19, "customer_idx": 3, "created": hrs_ago(3)},
    # Waiting on customer
    {"subject": "Need clarification on SSO setup steps",        "status": "waiting_customer", "channel": "email",    "priority": "medium",   "sentiment":  0.12, "customer_idx": 6, "created": hrs_ago(5)},
    {"subject": "Bulk import — which CSV template to use?",     "status": "waiting_customer", "channel": "whatsapp", "priority": "low",      "sentiment":  0.28, "customer_idx": 7, "created": hrs_ago(6)},
    # Escalated
    {"subject": "Data not syncing after migration — production down", "status": "escalated",  "channel": "email",    "priority": "critical", "sentiment": -0.91, "customer_idx": 3, "created": hrs_ago(2),  "escalated_to": "tier-2-support"},
    {"subject": "Possible unauthorised access to account",       "status": "escalated",        "channel": "web_form", "priority": "critical", "sentiment": -0.87, "customer_idx": 0, "created": hrs_ago(1),  "escalated_to": "security-team"},
    {"subject": "Billing charged twice this month",              "status": "escalated",        "channel": "whatsapp", "priority": "high",     "sentiment": -0.74, "customer_idx": 4, "created": hrs_ago(3),  "escalated_to": "billing-team"},
    # Resolved
    {"subject": "How to change primary email address",           "status": "resolved",         "channel": "web_form", "priority": "low",      "sentiment":  0.68, "customer_idx": 2, "created": hrs_ago(7)},
    {"subject": "GitHub integration not showing latest commits", "status": "resolved",         "channel": "email",    "priority": "medium",   "sentiment":  0.45, "customer_idx": 1, "created": hrs_ago(8)},
    {"subject": "Slack notifications firing for every comment",  "status": "resolved",         "channel": "whatsapp", "priority": "medium",   "sentiment":  0.33, "customer_idx": 5, "created": hrs_ago(9)},
    {"subject": "Timeline view not rendering on Safari",         "status": "resolved",         "channel": "web_form", "priority": "high",     "sentiment":  0.51, "customer_idx": 6, "created": hrs_ago(10)},
    {"subject": "Account locked after too many login attempts",  "status": "resolved",         "channel": "email",    "priority": "high",     "sentiment":  0.39, "customer_idx": 7, "created": hrs_ago(11)},
    # Closed
    {"subject": "Request for enterprise contract renewal terms", "status": "closed",           "channel": "email",    "priority": "medium",   "sentiment":  0.72, "customer_idx": 3, "created": hrs_ago(20)},
    {"subject": "Feature request: dark mode for mobile app",    "status": "closed",           "channel": "web_form", "priority": "low",      "sentiment":  0.58, "customer_idx": 2, "created": hrs_ago(22)},
]


# ── Daily report ───────────────────────────────────────────────────────────────

REPORT = {
    "report_date":    date.today(),
    "total_tickets":  18,
    "resolved":       7,
    "escalated":      3,
    "avg_sentiment":  -0.08,
    "top_issues": [
        "Authentication & login failures",
        "Third-party integration errors (Zapier, GitHub)",
        "Billing discrepancies",
        "Data sync issues post-migration",
        "Notification delivery problems",
    ],
    "summary_text": (
        "Today saw elevated ticket volume with 18 inbound requests, up 20% from yesterday. "
        "Three tickets were escalated: two critical security and data-sync issues requiring Tier 2, "
        "and one billing dispute routed to the billing team. "
        "Resolution rate sits at 39% — within acceptable range but authentication failures are clustering "
        "across multiple Pro and Enterprise accounts, suggesting a potential issue with the recent SSO update. "
        "Average sentiment is slightly negative at -0.08, driven primarily by the two critical escalations. "
        "Recommend a proactive outreach to affected accounts before end of day."
    ),
}


# ── Seed function ──────────────────────────────────────────────────────────────

async def seed():
    await init_db()

    async with AsyncSessionLocal() as db:
        # Wipe existing demo data
        await db.execute(text("DELETE FROM daily_reports"))
        await db.execute(text("DELETE FROM messages"))
        await db.execute(text("DELETE FROM tickets"))
        await db.execute(text("DELETE FROM customers"))
        await db.commit()

        # Insert customers
        customer_ids = []
        for c in CUSTOMERS:
            cid = uuid.uuid4()
            customer_ids.append(cid)
            db.add(Customer(id=cid, **c))
        await db.commit()

        # Insert tickets
        for t in TICKETS:
            tid = uuid.uuid4()
            resolved_at = datetime.utcnow() if t["status"] in ("resolved", "closed") else None
            db.add(Ticket(
                id=tid,
                customer_id=customer_ids[t["customer_idx"]],
                subject=t["subject"],
                status=t["status"],
                channel=t["channel"],
                priority=t["priority"],
                sentiment_score=t["sentiment"],
                escalated_to=t.get("escalated_to"),
                resolved_at=resolved_at,
                created_at=t["created"],
            ))
        await db.commit()

        # Insert daily report
        db.add(DailyReport(id=uuid.uuid4(), **REPORT))
        await db.commit()

        print(f"Seeded {len(CUSTOMERS)} customers, {len(TICKETS)} tickets, 1 daily report.")


if __name__ == "__main__":
    asyncio.run(seed())
