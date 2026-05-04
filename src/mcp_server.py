"""
MCP Server — Customer Success FTE Agent

Exposes the CRM support agent capabilities over the Model Context Protocol.
Tools: search_knowledge_base, create_ticket, get_customer_history,
       escalate_to_human, send_response, get_ticket_status, get_dashboard

Run:
    python -m src.mcp_server          # stdio transport (default)
    python -m src.mcp_server --sse    # SSE transport (for remote access)
"""

from enum import Enum
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from src.core_loop_prototype import (
    IncomingMessage,
    classify_category,
    detect_language,
    estimate_sentiment,
    process_ticket,
)
from src.conversation_state import (
    ConversationMemory,
    ConversationSession,
    CustomerProfile,
)

# ── Shared state ───────────────────────────────────────────────────────────────

memory = ConversationMemory()
_tickets: dict[str, dict] = {}


# ── Enum / Models ──────────────────────────────────────────────────────────────

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KBResult(BaseModel):
    """A single knowledge base match."""
    category: str
    problem: str
    solution: str


class KBResponse(BaseModel):
    results: list[KBResult]


class TicketResponse(BaseModel):
    ticket_id: str
    status: str


class CustomerHistoryEntry(BaseModel):
    channel: str
    topic: str
    sentiment: float
    escalated: bool
    resolved: bool
    timestamp: str


class CustomerHistoryResponse(BaseModel):
    email: str
    name: str
    plan: str
    total_tickets: int
    sessions: int
    entries: list[CustomerHistoryEntry]


class EscalationResponse(BaseModel):
    escalation_id: str
    ticket_id: str
    queue: str


class SendResponse(BaseModel):
    delivery_status: str
    channel: str
    ticket_id: str


class TicketStatusResponse(BaseModel):
    ticket_id: str
    status: str
    category: str
    escalated: bool
    escalation_queue: str
    resolved: bool
    channels_used: list[str]


class DashboardResponse(BaseModel):
    active_sessions: int
    total_customers: int
    total_tickets: int
    escalated_tickets: int
    resolved_tickets: int
    avg_sentiment: float


# ── Server ─────────────────────────────────────────────────────────────────────

server = FastMCP(
    "customer-success-fte",
    instructions="CRM Customer Success FTE — AI-powered support ticket handling across email, WhatsApp, and web form.",
)


# ── Tools ──────────────────────────────────────────────────────────────────────

@server.tool()
def search_knowledge_base(query: str) -> KBResponse:
    """Search product documentation for relevant information.

    Use this before answering customer questions to ground responses
    in known solutions.

    Args:
        query: The search term or customer question.

    Returns:
        Matching KB entries with category, problem, and solution.
    """
    from src.core_loop_prototype import _find_kb, _KB_SEED

    results = []

    # Try exact KB match first
    kb_str = _find_kb(query)
    if kb_str:
        for kw, sol in _KB_SEED.items():
            if sol == kb_str:
                results.append(KBResult(
                    category=_guess_category(kw),
                    problem=kw,
                    solution=sol,
                ))
                break

    # Also keyword-match across all entries
    query_lower = query.lower()
    for kw, sol in _KB_SEED.items():
        kw_words = kw.lower().split()
        if any(w in query_lower for w in kw_words) and len(results) < 5:
            already = [r.problem for r in results]
            if kw not in already:
                results.append(KBResult(
                    category=_guess_category(kw),
                    problem=kw,
                    solution=sol,
                ))

    return KBResponse(results=results)


@server.tool()
def create_ticket(
    customer_id: str,
    issue: str,
    subject: str = "",
    channel: Channel = Channel.EMAIL,
    priority: Priority = Priority.MEDIUM,
    customer_name: str = "",
    phone: str = "",
    company: str = "",
    plan: str = "free",
) -> TicketResponse:
    """Create a support ticket and process it through the AI agent.

    The ticket is automatically classified, sentiment-scored, and if
    possible, resolved. Returns the ticket ID and initial status.

    Args:
        customer_id: Customer email address (primary identifier).
        issue: The customer's message or problem description.
        subject: Optional short subject line.
        channel: Source channel of the message.
        priority: Urgency level.
        customer_name: Customer display name.
        phone: Customer phone/WhatsApp number.
        company: Company name.
        plan: Customer's subscription plan.

    Returns:
        Ticket ID and current status.
    """
    msg = IncomingMessage(
        channel=channel.value,
        body=issue,
        sender_email=customer_id,
        sender_name=customer_name,
        subject=subject,
        phone=phone,
        company=company,
    )

    result = process_ticket(msg, customer_plan=plan, memory=memory)

    # Register in our ticket store
    session = memory.get_active_session(customer_id)
    _tickets[result.ticket_id] = {
        "ticket_id": result.ticket_id,
        "customer_email": customer_id,
        "subject": subject or issue[:80],
        "channel": channel.value,
        "status": "escalated" if result.escalated else "resolved" if result.resolved else "open",
        "category": result.category,
        "escalated": result.escalated,
        "escalation_queue": result.escalation_queue,
        "resolved": result.resolved,
        "language": result.language,
        "sentiment": result.metadata.get("sentiment", 0.0),
        "session_id": session.session_id if session else "",
    }

    return TicketResponse(
        ticket_id=result.ticket_id,
        status=_tickets[result.ticket_id]["status"],
    )


@server.tool()
def get_customer_history(customer_id: str) -> CustomerHistoryResponse:
    """Get a customer's complete interaction history across ALL channels.

    Returns session history, sentiment trend, topics discussed,
    and resolution status. Use the customer's email address as the ID.

    Args:
        customer_id: Customer email address.

    Returns:
        Full interaction history with per-turn detail.
    """
    profile = memory.get_profile(customer_id)
    if not profile:
        profile = memory.get_or_create_profile(customer_id)

    # Build entries from session turns
    entries = []
    for session in memory.get_customer_history(customer_id):
        for turn in session.turns:
            entries.append(CustomerHistoryEntry(
                channel=turn.channel,
                topic=turn.topic_detected,
                sentiment=turn.sentiment_score,
                escalated=turn.escalated,
                resolved=turn.resolved,
                timestamp=turn.timestamp,
            ))

    # Also include active session turns
    active = memory.get_active_session(customer_id)
    if active:
        for turn in active.turns:
            entries.append(CustomerHistoryEntry(
                channel=turn.channel,
                topic=turn.topic_detected,
                sentiment=turn.sentiment_score,
                escalated=turn.escalated,
                resolved=turn.resolved,
                timestamp=turn.timestamp,
            ))

    return CustomerHistoryResponse(
        email=profile.customer_email,
        name=profile.customer_name,
        plan=profile.plan,
        total_tickets=profile.total_tickets,
        sessions=len(memory.get_customer_history(customer_id)) + (1 if active else 0),
        entries=entries,
    )


@server.tool()
def escalate_to_human(
    ticket_id: str,
    reason: str,
    queue: str = "tier-2-support",
) -> EscalationResponse:
    """Escalate a ticket to a human agent queue.

    Call this when the AI cannot resolve an issue, or when the
    customer needs human intervention (billing disputes, legal
    requests, security incidents, or repeated failures).

    Args:
        ticket_id: The ticket to escalate.
        reason: Why this ticket needs human intervention.
        queue: Which human queue to route to (default: tier-2-support).
               Options: legal-team, security-team, billing-team,
               enterprise-csm, tier-2-support.

    Returns:
        Escalation ID and routing information.
    """
    ticket = _tickets.get(ticket_id)
    if not ticket:
        # Create a minimal ticket record if it doesn't exist
        ticket = {
            "ticket_id": ticket_id,
            "customer_email": "",
            "status": "escalated",
            "category": "general",
            "escalated": True,
            "escalation_queue": queue,
            "resolved": False,
            "channels_used": ["email"],
        }

    escalation_id = f"ESC-{ticket_id}"

    ticket["status"] = "escalated"
    ticket["escalated"] = True
    ticket["escalation_queue"] = queue

    return EscalationResponse(
        escalation_id=escalation_id,
        ticket_id=ticket_id,
        queue=queue,
    )


@server.tool()
def send_response(
    ticket_id: str,
    message: str,
    channel: Channel,
) -> SendResponse:
    """Send a response to a customer via the appropriate channel.

    This tool is used to queue a message for delivery. In production,
    this connects to the channel-specific API (Gmail, WhatsApp, web form).

    Args:
        ticket_id: The ticket to respond to.
        message: The response text to send.
        channel: Which channel to deliver on.

    Returns:
        Delivery status confirmation.
    """
    ticket = _tickets.get(ticket_id, {"ticket_id": ticket_id})
    ticket["channels_used"] = [channel.value]

    # Simulate delivery confirmation
    return SendResponse(
        delivery_status="queued",
        channel=channel.value,
        ticket_id=ticket_id,
    )


@server.tool()
def get_ticket_status(ticket_id: str) -> TicketStatusResponse:
    """Look up the current status of a ticket.

    Returns full ticket details including category, escalation state,
    resolution status, and which channels have been used.

    Args:
        ticket_id: The ticket ID to look up.

    Returns:
        Complete ticket status.
    """
    ticket = _tickets.get(ticket_id)
    if not ticket:
        return TicketStatusResponse(
            ticket_id=ticket_id,
            status="not_found",
            category="",
            escalated=False,
            escalation_queue="",
            resolved=False,
            channels_used=[],
        )

    return TicketStatusResponse(
        ticket_id=ticket["ticket_id"],
        status=ticket["status"],
        category=ticket.get("category", ""),
        escalated=ticket.get("escalated", False),
        escalation_queue=ticket.get("escalation_queue", ""),
        resolved=ticket.get("resolved", False),
        channels_used=ticket.get("channels_used", [ticket.get("channel", "")]),
    )


@server.tool()
def get_dashboard() -> DashboardResponse:
    """Get a high-level overview of all active support operations.

    Returns counts of sessions, customers, tickets by status,
    and average sentiment across all active conversations.

    Returns:
        Dashboard statistics.
    """
    all_sessions = list(memory._active_sessions.values())
    total_tickets = len(_tickets)
    escalated = sum(1 for t in _tickets.values() if t.get("escalated"))
    resolved = sum(1 for t in _tickets.values() if t.get("resolved"))

    sentiments = []
    for s in all_sessions:
        sentiments.extend(s.sentiment_track)
    avg_sent = sum(sentiments) / len(sentiments) if sentiments else 0.0

    return DashboardResponse(
        active_sessions=len(all_sessions),
        total_customers=len(memory._customers),
        total_tickets=total_tickets,
        escalated_tickets=escalated,
        resolved_tickets=resolved,
        avg_sentiment=round(avg_sent, 3),
    )


@server.tool()
def process_customer_message(
    customer_email: str,
    message: str,
    channel: Channel = Channel.EMAIL,
    customer_name: str = "",
    plan: str = "free",
) -> TicketResponse:
    """Process an incoming customer message end-to-end.

    This is the main entry point. It creates a ticket, runs it through
    the AI core loop (language detection, escalation scanning, KB search,
    reply generation), and records the conversation turn.

    Use this for incoming messages that need an AI response. Use
    create_ticket for more control over priority and metadata.

    Args:
        customer_email: Customer email address.
        message: The customer's message text.
        channel: Which channel the message came from.
        customer_name: Customer display name (optional).
        plan: Customer subscription plan (free/starter/pro/enterprise).

    Returns:
        Ticket ID and status.
    """
    msg = IncomingMessage(
        channel=channel.value,
        body=message,
        sender_email=customer_email,
        sender_name=customer_name,
    )

    result = process_ticket(msg, customer_plan=plan, memory=memory)

    session = memory.get_active_session(customer_email)
    _tickets[result.ticket_id] = {
        "ticket_id": result.ticket_id,
        "customer_email": customer_email,
        "subject": message[:80],
        "channel": channel.value,
        "status": "escalated" if result.escalated else "resolved" if result.resolved else "open",
        "category": result.category,
        "escalated": result.escalated,
        "escalation_queue": result.escalation_queue,
        "resolved": result.resolved,
        "language": result.language,
        "sentiment": result.metadata.get("sentiment", 0.0),
        "session_id": session.session_id if session else "",
    }

    return TicketResponse(
        ticket_id=result.ticket_id,
        status=_tickets[result.ticket_id]["status"],
    )


# ── Helper ─────────────────────────────────────────────────────────────────────

def _guess_category(kb_key: str) -> str:
    """Map a KB keyword to its likely category."""
    key_lower = kb_key.lower()
    if "password" in key_lower or "reset" in key_lower or "login" in key_lower:
        return "login"
    if "jira" in key_lower or "github" in key_lower or "integration" in key_lower:
        return "integrations"
    if "automation" in key_lower or "trigger" in key_lower:
        return "automations"
    if "billing" in key_lower or "plan" in key_lower or "trial" in key_lower:
        return "billing"
    if "timeline" in key_lower or "gantt" in key_lower:
        return "views"
    if "mobile" in key_lower:
        return "mobile"
    if "data" in key_lower or "export" in key_lower:
        return "data"
    return "general"


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if "--sse" in sys.argv:
        host = "127.0.0.1"
        port = 8000
        print(f"Starting Customer Success FTE MCP server on http://{host}:{port} (SSE mode)")
        server.run(transport="sse", host=host, port=port)
    else:
        print("Starting Customer Success FTE MCP server (stdio mode)...")
        server.run()
