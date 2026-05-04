"""
Agent tool functions — the Customer Success FTE's capabilities.

Each function is registered as a Gemini function-calling tool.
The agent decides which tools to call based on the incoming ticket.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    Customer, DailyReport, KnowledgeBase, Message, MessageRole,
    Ticket, TicketPriority, TicketStatus,
)


# ── Customer lookup / creation ─────────────────────────────────────────────────

async def get_or_create_customer(
    db: AsyncSession,
    email: str,
    name: str = "",
    phone: str = "",
    company: str = "",
) -> dict:
    """
    Look up a customer by email. Creates a new record if not found.
    Returns customer dict with id, name, email, plan, company.
    """
    result = await db.execute(select(Customer).where(Customer.email == email))
    customer = result.scalar_one_or_none()

    if not customer:
        customer = Customer(
            email=email, name=name, phone=phone, company=company
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

    return {
        "id": str(customer.id),
        "email": customer.email,
        "name": customer.name or "",
        "company": customer.company or "",
        "plan": customer.plan or "free",
    }


# ── Ticket management ──────────────────────────────────────────────────────────

async def create_ticket(
    db: AsyncSession,
    customer_id: str,
    channel: str,
    subject: str,
    body: str,
    priority: str = "medium",
) -> dict:
    """
    Create a new support ticket and log the first customer message.
    Returns ticket dict with id and status.
    """
    ticket = Ticket(
        customer_id=uuid.UUID(customer_id),
        channel=channel,
        subject=subject,
        priority=priority,
        status=TicketStatus.open,
    )
    db.add(ticket)
    await db.flush()

    msg = Message(
        ticket_id=ticket.id,
        role=MessageRole.customer,
        body=body,
    )
    db.add(msg)
    await db.commit()

    return {"ticket_id": str(ticket.id), "status": ticket.status, "priority": priority}


async def update_ticket_status(
    db: AsyncSession,
    ticket_id: str,
    status: str,
    escalated_to: str = "",
) -> dict:
    """
    Update a ticket's status (e.g. open → in_progress → resolved).
    Pass escalated_to when routing to a human agent.
    """
    result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
    ticket = result.scalar_one_or_none()
    if not ticket:
        return {"error": f"Ticket {ticket_id} not found"}

    ticket.status = status
    if escalated_to:
        ticket.escalated_to = escalated_to
    if status == TicketStatus.resolved:
        ticket.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    return {"ticket_id": ticket_id, "new_status": status}


async def set_ticket_sentiment(
    db: AsyncSession,
    ticket_id: str,
    score: float,
) -> dict:
    """
    Store a sentiment score on the ticket (-1.0 = very negative, 1.0 = very positive).
    """
    result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
    ticket = result.scalar_one_or_none()
    if not ticket:
        return {"error": "Ticket not found"}
    ticket.sentiment_score = score
    await db.commit()
    return {"ticket_id": ticket_id, "sentiment_score": score}


async def get_customer_history(
    db: AsyncSession,
    customer_id: str,
    limit: int = 5,
) -> dict:
    """
    Fetch a customer's recent ticket history so the agent can personalise responses.
    Returns list of recent tickets with subject, status, and channel.
    """
    result = await db.execute(
        select(Ticket)
        .where(Ticket.customer_id == uuid.UUID(customer_id))
        .order_by(Ticket.created_at.desc())
        .limit(limit)
    )
    tickets = result.scalars().all()
    return {
        "tickets": [
            {
                "id": str(t.id),
                "subject": t.subject,
                "status": t.status,
                "channel": t.channel,
                "priority": t.priority,
                "created_at": t.created_at.isoformat() if t.created_at else "",
            }
            for t in tickets
        ]
    }


# ── Knowledge base ─────────────────────────────────────────────────────────────

async def search_knowledge_base(
    db: AsyncSession,
    category: str = "",
    keyword: str = "",
) -> dict:
    """
    Search the knowledge base for relevant past solutions.
    Use this before crafting a reply to find known fixes.
    """
    query = select(KnowledgeBase)
    if category:
        query = query.where(KnowledgeBase.category == category)
    if keyword:
        query = query.where(
            KnowledgeBase.problem.ilike(f"%{keyword}%")
            | KnowledgeBase.solution.ilike(f"%{keyword}%")
        )
    query = query.order_by(KnowledgeBase.usefulness.desc()).limit(3)
    result = await db.execute(query)
    entries = result.scalars().all()
    return {
        "results": [
            {"id": str(e.id), "category": e.category, "problem": e.problem, "solution": e.solution}
            for e in entries
        ]
    }


async def add_to_knowledge_base(
    db: AsyncSession,
    ticket_id: str,
    category: str,
    problem: str,
    solution: str,
) -> dict:
    """
    After resolving a ticket, save the problem/solution pair so the agent learns.
    """
    entry = KnowledgeBase(
        source_ticket=uuid.UUID(ticket_id),
        category=category,
        problem=problem,
        solution=solution,
    )
    db.add(entry)
    await db.commit()
    return {"kb_id": str(entry.id), "category": category}


# ── Message logging ────────────────────────────────────────────────────────────

async def log_agent_reply(
    db: AsyncSession,
    ticket_id: str,
    body: str,
) -> dict:
    """Log the agent's outbound reply to the ticket's message history."""
    msg = Message(
        ticket_id=uuid.UUID(ticket_id),
        role=MessageRole.agent,
        body=body,
    )
    db.add(msg)
    await db.commit()
    return {"logged": True, "ticket_id": ticket_id}


# ── Escalation ────────────────────────────────────────────────────────────────

async def escalate_ticket(
    db: AsyncSession,
    ticket_id: str,
    reason: str,
    queue: str = "tier-2-support",
) -> dict:
    """
    Escalate a ticket to a human agent queue.
    Call this when: customer is very angry, issue is billing/legal/security,
    or the agent cannot resolve after 2 attempts.
    """
    await update_ticket_status(db, ticket_id, TicketStatus.escalated, escalated_to=queue)
    await log_agent_reply(
        db, ticket_id,
        f"I've escalated your case to our {queue} team. Reason: {reason}. "
        "A human agent will reach out within 1 business day."
    )
    return {"escalated": True, "queue": queue, "reason": reason}


# ── Tool registry (maps name → function for Gemini function calling) ───────────

TOOL_REGISTRY: dict[str, Any] = {
    "get_or_create_customer": get_or_create_customer,
    "create_ticket": create_ticket,
    "update_ticket_status": update_ticket_status,
    "set_ticket_sentiment": set_ticket_sentiment,
    "get_customer_history": get_customer_history,
    "search_knowledge_base": search_knowledge_base,
    "add_to_knowledge_base": add_to_knowledge_base,
    "log_agent_reply": log_agent_reply,
    "escalate_ticket": escalate_ticket,
}
