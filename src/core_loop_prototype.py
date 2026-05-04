"""
Core Interaction Loop — Exercise 1.2 Prototype

Lightweight rules-based prototype. Demonstrates every aspect of the core loop
without requiring Gemini API. Swap in the Gemini-backed version in
`src/agent/core_loop.py` once the interaction shape is validated.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from src.conversation_state import ConversationMemory, ConversationTurn


# ── Data Models ────────────────────────────────────────────────────────────────

@dataclass
class IncomingMessage:
    channel: str            # "email" | "whatsapp" | "web_form"
    body: str
    sender_email: str
    sender_name: str
    subject: str = ""
    phone: str = ""
    company: str = ""


@dataclass
class TicketContext:
    language: str = "English"
    sentiment: float = 0.0
    needs_escalation: bool = False
    escalation_queue: str = ""
    escalation_reason: str = ""
    category: str = ""


@dataclass
class Response:
    ticket_id: str
    customer_name: str
    body: str
    language: str = "English"
    escalated: bool = False
    escalation_queue: str = ""
    category: str = ""
    resolved: bool = False
    metadata: dict = field(default_factory=dict)


# ── Keyword Scanners ──────────────────────────────────────────────────────────

_IMMEDIATE_ESCALATION = {
    "legal-team": re.compile(
        r"\b(attorney|lawsuit|court|legal notice|put you on notice|small claims"
        r"|subpoena|gdpr|dsar|data subject access|data deletion request"
        r"|dpa|baa|compliance request|ip claim|copyright|terms of service)\b",
        re.IGNORECASE,
    ),
    "security-team": re.compile(
        r"\b(breach|unauthorized access|hacked|account compromise|suspicious login"
        r"|unknown device|unknown location|someone else logged in"
        r"|sso.*locked out|locked out.*sso|emergency override|sso.*can.t authenticate)\b",
        re.IGNORECASE,
    ),
    "billing-team": re.compile(
        r"\b(double charged|charged twice|overcharged|refund|chargeback|dispute"
        r"|billing dispute|renewal discount|contract renewal|annual discount)\b",
        re.IGNORECASE,
    ),
}

_NEGATIVE_PATTERNS = re.compile(
    r"\b(unacceptable|ridiculous|frustrated|disaster|furious|angry|terrible"
    r"|useless|awful|horrible|fed up|give me a manager|speak to a human"
    r"|cancel.*review|1\.?star|third time|still not fixed)\b",
    re.IGNORECASE,
)

_LANGUAGE_HINTS = {
    "Spanish": re.compile(r"\b(cuando|como|integracion|quiero|necesito|por favor|hola)\b", re.IGNORECASE),
    "French": re.compile(r"\b(je suis|je veux|bonjour|merci|s'il|pouvez|vous|l'int[eé]gration|erreur)\b"),
    "Portuguese": re.compile(r"\b(obrigada|obrigado|ola |ola,|por favor)\b", re.IGNORECASE),
}

_CATEGORY_HINTS = [
    ("automations", re.compile(r"\b(automations?|automate|trigger|firing)\b", re.IGNORECASE)),
    ("integrations", re.compile(r"\b(slack|jira|github|gitlab|zapier|integration|webhook|sync|connect)\b", re.IGNORECASE)),
    ("billing", re.compile(r"\b(bill|invoice|payment|plan|upgrade|downgrade|price|cost|charge|subscription|trial)\b", re.IGNORECASE)),
    ("login", re.compile(r"\b(login|password|reset|2fa|two.factor|forgot|sign.in|locked.out|sso)\b", re.IGNORECASE)),
    ("mobile", re.compile(r"\b(mobile|app|ios|android|phone|tablet|offline|push notification)\b", re.IGNORECASE)),
    ("views", re.compile(r"\b(timeline|gantt|calendar|kanban|board|my work)\b", re.IGNORECASE)),
    ("data", re.compile(r"\b(export|import|csv|download|backup|migrate)\b", re.IGNORECASE)),
    ("feature_request", re.compile(r"\b(feature|dark.mode|recurring|recurring task|recurring tasks)\b", re.IGNORECASE)),
]

_PLAN_LIMITS = {
    "free":       {"users": 3,  "automations": 0,  "storage": "10MB/file",  "integrations": []},
    "starter":    {"users": 10, "automations": 50, "storage": "50MB/file", "integrations": ["slack", "gmail", "zapier"]},
    "pro":        {"users": 50, "automations": float("inf"), "storage": "250MB/file", "integrations": ["slack", "gmail", "zapier", "jira", "github"]},
    "enterprise": {"users": float("inf"), "automations": float("inf"), "storage": "unlimited", "integrations": ["all"]},
}

_PLAN_FEATURES = {
    "timeline_gantt": ["pro", "enterprise"],
    "github": ["pro", "enterprise"],
    "jira": ["pro", "enterprise"],
    "automations": ["starter", "pro", "enterprise"],
    "zapier": ["starter", "pro", "enterprise"],
    "custom_fields": ["starter", "pro", "enterprise"],
    "sso": ["enterprise"],
    "eu_data": ["enterprise"],
}

# Simple KB seeded from product-docs.md seeded patterns
_KB_SEED = {
    "password reset": "Go to flowdesk.io/login → 'Forgot password'. A reset link will be sent (valid 1 hour). Check spam if it doesn't arrive within 2 minutes.",
    "jira duplicate": "Known first-sync bug: Jira creates duplicates on initial connect. Delete duplicates and re-sync to fix.",
    "firefox bug": "Known Firefox upgrade bug. Workaround: use Chrome or Safari for the upgrade flow.",
    "data retention": "Data is retained for 90 days after cancellation. Export before then from Settings → Billing.",
    "trial": "New accounts automatically get a 14-day Pro trial. No credit card required. After trial, the account reverts to Free.",
    "automation limits": "Free: no automations. Starter: 50 runs/month. Pro: unlimited. Monthly reset on the 1st.",
    "timeline": "Timeline/Gantt view is available on Pro and Enterprise plans only.",
    "github integration": "GitHub integration is available on Pro and Enterprise. Connect via Settings → Integrations → GitHub.",
    "invite expiry": "Team invites are valid for 7 days. Resend from Settings → Team.",
    "mobile limits": "Timeline not available on mobile. Automations can be viewed but not created on the mobile app. Read-only offline mode.",
}


# ── Core Pipeline ─────────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    for lang, pattern in _LANGUAGE_HINTS.items():
        if pattern.search(text):
            return lang
    return "English"


def check_escalation(text: str) -> tuple[bool, str, str]:
    for queue, pattern in _IMMEDIATE_ESCALATION.items():
        if pattern.search(text):
            reason_map = {
                "legal-team": "Legal or compliance trigger",
                "security-team": "Security incident trigger",
                "billing-team": "Billing dispute trigger",
            }
            return True, queue, reason_map.get(queue, "Trigger detected")
    return False, "", ""


def classify_category(text: str) -> str:
    for category, pattern in _CATEGORY_HINTS:
        if pattern.search(text):
            return category
    return "general"


def estimate_sentiment(text: str) -> float:
    matches = _NEGATIVE_PATTERNS.findall(text)
    if matches:
        return max(-1.0, -0.4 * len(matches))
    return 0.0


def _find_kb(text: str) -> Optional[str]:
    text_lower = text.lower()
    for keyword, solution in _KB_SEED.items():
        # Match individual words from multi-word keywords
        kw_words = keyword.lower().split()
        if all(w in text_lower or (w.endswith("e") and w[:-1] + "d" in text_lower) for w in kw_words):
            return solution
    return None


def _build_reply(
    channel: str,
    customer_name: str,
    category: str,
    kb: Optional[str],
    escalation_needed: bool,
    escalation_queue: str,
    escalation_reason: str,
    sentiment: float,
    language: str,
    needs_plan_check: bool,
    customer_plan: str,
) -> str:
    """Format the reply based on all context signals."""

    # ── Escalation path
    if escalation_needed:
        public_name = {
            "legal-team": "a compliance specialist",
            "security-team": "our security team",
            "billing-team": "our billing specialist",
        }.get(escalation_queue, "a specialist team")
        return _format_escalation(channel, customer_name, public_name, language)

    # Resolution path
    if kb:
        body = kb
    else:
        body = _generic_reply(category, customer_plan)

    # empathy for negative sentiment
    if sentiment < -0.5:
        body = (
            f"Hi {customer_name.split()[0] if customer_name else ''}, "
            f"I'm really sorry you're going through this — I understand how frustrating it must be. "
            f"{body}"
        )
    elif customer_name and sentiment >= -0.3:
        body = f"Hi {customer_name.split()[0]},\n\n{body}"

    return _sign_off(channel, body)


def _format_escalation(channel: str, name: str, specialist: str, language: str) -> str:
    first = name.split()[0] if name else "there"
    base = (
        f"Hi {first}, I've reviewed your message and I want to make sure you get the right help. "
        f"I've looped in {specialist} who will follow up with you directly within 24 hours. "
        f"Your case has been prioritised."
    )
    return _sign_off(channel, base)


def _sign_off(channel: str, body: str) -> str:
    if channel == "email":
        body += "\n\nBest,\nAlex\nFlowDesk Customer Success"
    elif channel == "whatsapp":
        body += "\n\n— Alex, FlowDesk"
    # web_form: no sign-off
    return body


def _generic_reply(category: str, plan: str) -> str:
    """Fallback replies for categories without a KB match."""
    replies = {
        "automations": _auto_reply(plan),
        "billing": _billing_reply(plan),
        "login": "Try resetting your password at flowdesk.io/login → 'Forgot password'. If you're still stuck, I can loop in a specialist.",
        "integrations": "For integration issues, try reconnecting from Settings → Integrations. If the problem persists, a specialist can help.",
        "mobile": "The mobile app (iOS 15+, Android 10+) supports most features but not Timeline or creating automations. If it's a crash, try reinstalling.",
        "views": "Timeline/Gantt is available on Pro+. Calendar view is on all plans.",
        "data": "You can export data from Settings → Export → CSV. Google Sheets integration is coming soon.",
        "feature_request": "Thanks for the suggestion — I'll pass it along to the product team! We review all feedback each quarter.",
        "general": "Thanks for reaching out. I've logged your case and will follow up shortly. If you need urgent help, reply on this thread.",
    }
    return replies.get(category, replies["general"])


def _auto_reply(plan: str) -> str:
    limits = _PLAN_LIMITS.get(plan, _PLAN_LIMITS["free"])
    auto = limits["automations"]
    if auto == 0:
        return "The Free plan doesn't include automations. You'll need to upgrade to Starter (50 runs/month) or Pro (unlimited). You'll still be in your 14-day Pro trial if the account is new."
    elif auto == 50:
        return ("Your Starter plan allows 50 automation runs per month. If you've hit the limit, "
                "you can upgrade to Pro for unlimited runs or wait for the monthly reset on the 1st.")
    return ("Your Pro plan includes unlimited automations. If one isn't firing, check: is the toggle enabled? "
            "Does the trigger match exactly? Any duplicate rules might be double-firing.")


def _billing_reply(plan: str) -> str:
    return ("You can manage your plan and invoices from Settings → Billing. "
            f"You're currently on the {plan} plan. "
            "For billing questions beyond plan changes, I'll connect you with billing.")


# ── Main Pipeline ──────────────────────────────────────────────────────────────

def process_ticket(
    msg: IncomingMessage,
    customer_plan: str = "free",
    ticket_id: str = "",
    memory: Optional[ConversationMemory] = None,
) -> Response:
    """
    The core interaction loop for a single incoming message.

    Steps:
      1. Detect language
      2. Assess sentiment
      3. KEYWORD SCAN -- legal/security/billing escalation before anything else
      4. Classify category
      5. Check plan limits for feature-related queries
      6. Search KB
      7. Build response
      8. Record turn in conversation memory (if provided)
    """

    if not ticket_id:
        ticket_id = f"TICK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Step 1
    language = detect_language(msg.body)

    # Step 2
    sentiment = estimate_sentiment(msg.body)

    # Step 3 -- ESCALATION FIRST (before answering)
    needs_escalation, escalate_queue, escalate_reason = check_escalation(msg.body)

    # Step 4
    category = classify_category(msg.body)

    # Step 5 -- feature queries that depend on plan
    needs_plan_check = any(
        f in msg.body.lower() for f in
        ["automation", "timeline", "gantt", "github", "jira", "sso", "zapier", "custom field", "export"]
    )

    # Step 6 -- KB search
    kb_match = _find_kb(msg.body)

    # Check if plan blocks the feature
    if needs_plan_check and not needs_escalation:
        plan_blocked = False
        for feature_key, allowed_plans in _PLAN_FEATURES.items():
            if feature_key in msg.body.lower() and customer_plan not in allowed_plans:
                plan_blocked = True
                break
        if plan_blocked:
            kb_match = _generic_reply(category, customer_plan)

    # Step 7 -- build response
    body = _build_reply(
        channel=msg.channel,
        customer_name=msg.sender_name,
        category=category,
        kb=kb_match,
        escalation_needed=needs_escalation,
        escalation_queue=escalate_queue,
        escalation_reason=escalate_reason,
        sentiment=sentiment,
        language=language,
        needs_plan_check=needs_plan_check,
        customer_plan=customer_plan,
    )

    # Step 8 -- record in conversation memory
    if memory is not None:
        email = msg.sender_email
        profile = memory.get_or_create_profile(email, name=msg.sender_name, phone=msg.phone, company=msg.company, plan=customer_plan)
        session = memory.get_active_session(email)
        if session is None:
            session = memory.create_session(email, msg.channel, msg.sender_name)
        memory.record_turn(
            session,
            message_body=msg.body,
            reply_body=body,
            channel=msg.channel,
            topic=category,
            sentiment=sentiment,
            escalated=needs_escalation,
            resolved=not needs_escalation,
        )

    return Response(
        ticket_id=ticket_id,
        customer_name=msg.sender_name,
        body=body,
        language=language,
        escalated=needs_escalation,
        escalation_queue=escalate_queue,
        category=category,
        resolved=not needs_escalation,
        metadata={
            "sentiment": sentiment,
            "plan": customer_plan,
            "kb_matched": kb_match is not None,
            "plan_check": needs_plan_check,
        },
    )
