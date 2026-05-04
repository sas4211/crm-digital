"""
Core Interaction Loop — Exercise 1.2 prototype.

Implements every step crystallised during the discovery phase:
  1. Language detection
  2. Customer lookup
  3. Sentiment scoring
  4. KEYWORD SCAN (legal/security — immediate escalation before any other processing)
  5. Category classification
  6. Plan-aware KB search
  7. Gemini function-calling agent turn
  8. Channel-aware reply formatting
  9. Logging + KB write-back on resolution
"""

import os
import re
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.tools import (
    add_to_knowledge_base,
    create_ticket,
    escalate_ticket,
    get_or_create_customer,
    log_agent_reply,
    search_knowledge_base,
    set_ticket_sentiment,
    update_ticket_status,
)
from src.agent.tool_schemas import GEMINI_TOOLS
from src.db.models import TicketStatus


# ── Constants ──────────────────────────────────────────────────────────────────

# Regex patterns for immediate-escalation triggers (keyword scan step 4)
_LEGAL_PATTERNS = re.compile(
    r"\b(attorney|lawsuit|court|legal notice|put you on notice|small claims"
    r"|subpoena|gdpr|dsar|data subject access|data deletion request"
    r"|dpa|baa|compliance request|ip claim|copyright)\b",
    re.IGNORECASE,
)
_SECURITY_PATTERNS = re.compile(
    r"\b(breach|unauthorized access|hacked|account compromise|suspicious login"
    r"|unknown device|unknown location|someone else logged in)\b",
    re.IGNORECASE,
)
_BILLING_ESCALATE_PATTERNS = re.compile(
    r"\b(double charged|charged twice|overcharged|refund|chargeback|dispute"
    r"|billing dispute|renewal discount|contract renewal|annual discount)\b",
    re.IGNORECASE,
)

# Sentiment keywords (simple heuristic before Gemini scores it)
_NEGATIVE_WORDS = re.compile(
    r"\b(unacceptable|ridiculous|frustrated|disaster|furious|angry|terrible"
    r"|useless|awful|horrible|fed up|give me a manager|speak to a human"
    r"|cancel.*review|1.star)\b",
    re.IGNORECASE,
)

# Channel-specific sign-off templates
_SIGN_OFFS = {
    "email": "\n\nBest,\nAlex\nFlowDesk Customer Success",
    "whatsapp": "\n\n— Alex, FlowDesk",
    "web_form": "",  # No sign-off; ticket ID shown separately
}


# ── System prompts per channel ────────────────────────────────────────────────

def _build_system_prompt(channel: str, plan: str, language: str) -> str:
    tone_instructions = {
        "email": (
            "You are writing a professional support email. Use paragraph structure, "
            "numbered steps for multi-step answers, and sign off as 'Best, Alex | FlowDesk Customer Success'. "
            "Keep replies under 150 words unless troubleshooting requires more detail."
        ),
        "whatsapp": (
            "You are responding via WhatsApp. Keep messages SHORT — 2-4 sentences max. "
            "Use line breaks between ideas. Casual, warm tone. "
            "You may use 1 emoji if it fits naturally. Never more. "
            "Sign off as '— Alex, FlowDesk' only for escalation messages."
        ),
        "web_form": (
            "Your reply will be shown inline on the support form page. "
            "Be direct — start with the resolution or next step. "
            "No sign-off needed; the ticket ID will be shown separately."
        ),
    }

    return f"""You are Alex, a Customer Success AI employee at FlowDesk, a project management SaaS.
You respond to support tickets 24/7 across email, WhatsApp, and web form.

CUSTOMER'S PLAN: {plan.upper()}
CUSTOMER'S LANGUAGE: {language}
CHANNEL: {channel}

RESPONSE LANGUAGE: Always respond in {language}. Never switch languages.

TONE & FORMAT FOR THIS CHANNEL:
{tone_instructions.get(channel, tone_instructions["email"])}

YOUR CORE RULES:
1. Use the customer's first name once, naturally.
2. Lead with the resolution or action — don't bury it.
3. Never say "I'm an AI", "as a language model", or "I cannot do that".
4. Never promise release dates, specific bug fix timelines, or discounts.
5. If the knowledge base has a relevant solution, use it and build on it.
6. After resolving: update ticket to 'resolved', save the solution to the KB.
7. If you cannot resolve after your best attempt: escalate. Do not guess or make things up.

PRODUCT FACTS YOU MUST KNOW:
- Plans: Free (3 users, no automations), Starter ($29, 10 users, 50 auto/mo), Pro ($79, 50 users, unlimited auto), Enterprise (custom)
- Timeline/Gantt view: Pro+ only
- GitHub integration: Pro+ only
- Zapier: Starter+ only
- Automations: Starter+ only
- Custom fields: Starter+ only
- SSO: Enterprise only
- EU data residency: Enterprise only
- API: Starter+ only
- Mobile: iOS 15+, Android 10+; Timeline not available on mobile
- Jira first-sync known issue: duplicates on first connect — delete duplicates and re-sync
- Firefox upgrade bug: known — workaround is Chrome or Safari
- Data retained 90 days after cancellation
- Password reset links valid 1 hour
- Team invites valid 7 days
"""


# ── Language detection ─────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """
    Lightweight language detection using Gemini.
    Returns an ISO language name string (e.g. "English", "French", "Spanish").
    Falls back to "English" if detection fails.
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Detect the language of this text. Reply with only the language name in English (e.g. 'French', 'Spanish', 'English'). Text:\n{text[:300]}",
        )
        lang = (response.text or "").strip().strip("'\"")
        return lang if lang else "English"
    except Exception:
        return "English"


# ── Sentiment heuristic ────────────────────────────────────────────────────────

def quick_sentiment(text: str) -> float:
    """
    Fast regex-based sentiment estimate. Gemini tool call will refine this.
    Returns approximate score: -0.8 (very negative) to 0.0 (neutral).
    """
    if _NEGATIVE_WORDS.search(text):
        # Count how many negative signals
        matches = len(_NEGATIVE_WORDS.findall(text))
        return max(-1.0, -0.4 * matches)
    return 0.0


# ── Immediate escalation check ────────────────────────────────────────────────

def check_immediate_escalation(text: str) -> tuple[bool, str, str]:
    """
    Scan for legal/security/billing triggers BEFORE any other processing.
    Returns (should_escalate, queue, reason).
    """
    if _LEGAL_PATTERNS.search(text):
        return True, "legal-team", "Legal or compliance trigger detected in message"
    if _SECURITY_PATTERNS.search(text):
        return True, "security-team", "Security incident trigger detected in message"
    if _BILLING_ESCALATE_PATTERNS.search(text):
        return True, "billing-team", "Billing dispute or refund trigger detected in message"
    return False, "", ""


# ── Main core loop ─────────────────────────────────────────────────────────────

async def process_ticket(
    db: AsyncSession,
    channel: str,
    customer_email: str,
    customer_name: str,
    message_body: str,
    subject: str = "",
    phone: str = "",
    company: str = "",
    priority: str = "medium",
) -> dict:
    """
    Full core interaction loop. Called by all three channel handlers.

    Returns:
        {
            "ticket_id": str,
            "customer_id": str,
            "reply": str,
            "language": str,
            "sentiment": float,
            "escalated": bool,
            "escalate_queue": str,
            "category": str,
        }
    """

    # ── STEP 1: Language detection ────────────────────────────────────────────
    language = detect_language(message_body)

    # ── STEP 2: Customer lookup / creation ────────────────────────────────────
    customer = await get_or_create_customer(
        db, email=customer_email, name=customer_name, phone=phone, company=company
    )
    customer_id = customer["id"]
    plan = customer.get("plan", "free")
    first_name = (customer_name or "there").split()[0]

    # ── STEP 3: Quick sentiment estimate ─────────────────────────────────────
    sentiment_estimate = quick_sentiment(message_body)

    # ── STEP 4: KEYWORD SCAN — immediate escalation? ──────────────────────────
    should_escalate, escalate_queue, escalate_reason = check_immediate_escalation(message_body)

    # ── Create the ticket now (always needed) ─────────────────────────────────
    ticket_result = await create_ticket(
        db,
        customer_id=customer_id,
        channel=channel,
        subject=subject or f"{channel.title()} inquiry from {customer_name}",
        body=message_body,
        priority="critical" if should_escalate else priority,
    )
    ticket_id = ticket_result["ticket_id"]

    # ── STEP 4b: Immediate escalation path ───────────────────────────────────
    if should_escalate:
        sla = _sla_by_plan(plan)
        reply = _escalation_reply(
            channel=channel,
            first_name=first_name,
            reason_public=_public_escalation_reason(escalate_queue),
            sla=sla,
            language=language,
        )
        await escalate_ticket(db, ticket_id=ticket_id, reason=escalate_reason, queue=escalate_queue)
        await log_agent_reply(db, ticket_id=ticket_id, body=reply)
        await set_ticket_sentiment(db, ticket_id=ticket_id, score=sentiment_estimate)
        return _result(ticket_id, customer_id, reply, language, sentiment_estimate, True, escalate_queue, "escalation")

    # ── STEP 5-7: KB search + Gemini agent turn ───────────────────────────────
    kb_results = await search_knowledge_base(db, keyword=_extract_keyword(message_body))
    reply, final_sentiment, category, resolved = await _agent_turn(
        db=db,
        ticket_id=ticket_id,
        customer_id=customer_id,
        channel=channel,
        plan=plan,
        language=language,
        first_name=first_name,
        message_body=message_body,
        subject=subject,
        kb_context=kb_results,
        sentiment_estimate=sentiment_estimate,
    )

    # ── STEP 9: Post-resolution KB write-back ─────────────────────────────────
    if resolved and category:
        await add_to_knowledge_base(
            db,
            ticket_id=ticket_id,
            category=category,
            problem=subject or message_body[:120],
            solution=reply[:500],
        )

    await set_ticket_sentiment(db, ticket_id=ticket_id, score=final_sentiment)

    return _result(ticket_id, customer_id, reply, language, final_sentiment, False, "", category)


# ── Gemini agent turn ─────────────────────────────────────────────────────────

async def _agent_turn(
    db: AsyncSession,
    ticket_id: str,
    customer_id: str,
    channel: str,
    plan: str,
    language: str,
    first_name: str,
    message_body: str,
    subject: str,
    kb_context: dict,
    sentiment_estimate: float,
) -> tuple[str, float, str, bool]:
    """
    Run Gemini with function calling to produce a reply.
    Returns (reply_text, sentiment_score, category, is_resolved).
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    chat = client.aio.chats.create(
        model="gemini-1.5-pro",
        config=types.GenerateContentConfig(
            system_instruction=_build_system_prompt(channel, plan, language),
            tools=GEMINI_TOOLS,
        ),
    )

    kb_summary = ""
    if kb_context.get("results"):
        kb_summary = "\n\nRelevant knowledge base entries:\n" + "\n".join(
            f"- [{r['category']}] {r['problem']} → {r['solution']}"
            for r in kb_context["results"]
        )

    initial_prompt = (
        f"Customer: {first_name} ({plan} plan)\n"
        f"Channel: {channel}\n"
        f"Subject: {subject}\n"
        f"Sentiment estimate: {sentiment_estimate:.1f}\n"
        f"Message:\n{message_body}"
        f"{kb_summary}\n\n"
        "Respond to this customer now. "
        "Call set_ticket_sentiment with your sentiment score. "
        "If you resolve the issue, call update_ticket_status with 'resolved'. "
        "If you cannot resolve, call escalate_ticket."
    )

    response = await chat.send_message(initial_prompt)

    # Process tool calls
    final_sentiment = sentiment_estimate
    category = "general"
    resolved = False

    for _ in range(8):
        if not _has_tool_calls(response):
            break

        tool_parts = []
        for part in (response.parts or []):
            if part.function_call is None:
                continue
            call = part.function_call
            name = call.name
            args = dict(call.args) if call.args else {}

            # Execute tool
            if name == "set_ticket_sentiment":
                final_sentiment = float(args.get("score", sentiment_estimate))
                result = await set_ticket_sentiment(db, ticket_id=ticket_id, score=final_sentiment)
            elif name == "update_ticket_status":
                result = await update_ticket_status(db, ticket_id=ticket_id, **args)
                if args.get("status") == TicketStatus.resolved:
                    resolved = True
            elif name == "escalate_ticket":
                result = await escalate_ticket(db, ticket_id=ticket_id, **args)
            elif name == "search_knowledge_base":
                result = await search_knowledge_base(db, **args)
            elif name == "add_to_knowledge_base":
                result = await add_to_knowledge_base(db, ticket_id=ticket_id, **args)
                category = args.get("category", category)
            elif name == "log_agent_reply":
                result = await log_agent_reply(db, ticket_id=ticket_id, **args)
            else:
                result = {"error": f"Unknown tool: {name}"}

            tool_parts.append(
                types.Part.from_function_response(
                    name=name,
                    response={"result": result},
                )
            )

        response = await chat.send_message(tool_parts)

    reply_text = _extract_text(response)

    # Apply channel sign-off
    reply_text = reply_text.rstrip() + _SIGN_OFFS.get(channel, "")

    # Log the reply
    await log_agent_reply(db, ticket_id=ticket_id, body=reply_text)

    return reply_text, final_sentiment, category, resolved


# ── Helpers ───────────────────────────────────────────────────────────────────

def _has_tool_calls(response) -> bool:
    return any(p.function_call is not None for p in (response.parts or []))


def _extract_text(response) -> str:
    return response.text or ""


def _extract_keyword(text: str) -> str:
    """Pull the most meaningful word from the message for KB search."""
    stopwords = {"i", "my", "the", "a", "an", "is", "in", "on", "at", "to", "we", "our"}
    words = [w.lower().strip("?.!,") for w in text.split() if len(w) > 4]
    return next((w for w in words if w not in stopwords), text[:20])


def _sla_by_plan(plan: str) -> str:
    return {
        "free": "2-3 business days",
        "starter": "48 hours",
        "pro": "12 hours",
        "enterprise": "4 hours",
    }.get(plan, "48 hours")


def _public_escalation_reason(queue: str) -> str:
    return {
        "legal-team": "a compliance specialist",
        "security-team": "our security team",
        "billing-team": "our billing specialist",
        "enterprise-csm": "your dedicated Customer Success Manager",
        "tier-2-support": "a senior support specialist",
    }.get(queue, "our specialist team")


def _escalation_reply(channel: str, first_name: str, reason_public: str, sla: str, language: str) -> str:
    # For multilingual escalation, we keep it in English and note specialist will follow up.
    # A real v2 would translate this too via Gemini.
    msg = (
        f"Hi {first_name}, I've reviewed your message and I want to make sure you get the right help. "
        f"I've looped in {reason_public} who will follow up with you directly. "
        f"You can expect to hear from them within {sla}. "
        f"Your case has been prioritised."
    )
    if channel == "email":
        msg += "\n\nBest,\nAlex\nFlowDesk Customer Success"
    elif channel == "whatsapp":
        msg += "\n\n— Alex, FlowDesk"
    return msg


def _result(
    ticket_id: str, customer_id: str, reply: str, language: str,
    sentiment: float, escalated: bool, escalate_queue: str, category: str
) -> dict:
    return {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "reply": reply,
        "language": language,
        "sentiment": sentiment,
        "escalated": escalated,
        "escalate_queue": escalate_queue,
        "category": category,
    }
