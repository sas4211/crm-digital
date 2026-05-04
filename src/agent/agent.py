"""
Customer Success FTE — Gemini-powered agent.

Uses Gemini function calling (tool use) to:
  1. Look up / create the customer
  2. Create a ticket
  3. Search the knowledge base
  4. Compose and send a reply
  5. Escalate if needed
  6. Log the resolution to the knowledge base
"""

import os
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.tools import TOOL_REGISTRY
from src.agent.tool_schemas import GEMINI_TOOLS

# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are Alex, a Customer Success AI employee at a SaaS company.
You work 24/7 and handle support tickets from email, WhatsApp, and the web form.

Your responsibilities:
1. Greet the customer warmly and acknowledge their issue.
2. Look up or create their customer record.
3. Create a ticket for their inquiry.
4. Check the knowledge base for known solutions.
5. Provide a clear, helpful, friendly reply.
6. Score the sentiment of the message (-1.0 to 1.0).
7. If you cannot resolve the issue in 1-2 exchanges, escalate to tier-2-support.
8. When resolved, save the problem/solution to the knowledge base.

Escalation triggers (escalate immediately, do not attempt to resolve):
- Billing disputes or refund requests
- Security or data breach concerns
- Legal or compliance questions
- Customer is abusive or threatening
- Technical issue requires engineering access

Tone: professional, empathetic, concise. Never use jargon. Always use the customer's name.
Output your reply text only — do not include JSON or metadata in the customer-facing reply.
"""


# ── Gemini client ──────────────────────────────────────────────────────────────

def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("Set GEMINI_API_KEY in your environment.")
    return genai.Client(api_key=api_key)


# ── Agentic loop ───────────────────────────────────────────────────────────────

async def run_agent(
    db: AsyncSession,
    customer_email: str,
    customer_name: str,
    channel: str,
    message_body: str,
    phone: str = "",
    company: str = "",
) -> dict:
    """
    Run the Customer Success agent on one incoming message.

    Returns:
        {
            "ticket_id": str,
            "reply": str,           # message sent back to customer
            "escalated": bool,
            "sentiment": float,
        }
    """
    client = _get_client()
    chat = client.aio.chats.create(
        model="gemini-1.5-pro-latest",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=GEMINI_TOOLS,
        ),
    )

    user_message = (
        f"New support ticket via {channel}.\n"
        f"Customer email: {customer_email}\n"
        f"Customer name: {customer_name}\n"
        f"Company: {company}\n"
        f"Phone: {phone}\n\n"
        f"Message:\n{message_body}"
    )

    state: dict[str, Any] = {
        "ticket_id": None,
        "reply": "",
        "escalated": False,
        "sentiment": 0.0,
    }

    response = await chat.send_message(user_message)

    for _ in range(10):  # max 10 tool-call rounds
        if not _has_tool_calls(response):
            state["reply"] = _extract_text(response)
            break

        tool_results = []
        for call in _get_tool_calls(response):
            result = await _dispatch(db, call, state)
            tool_results.append(
                types.Part.from_function_response(
                    name=call.name,
                    response={"result": result},
                )
            )

        response = await chat.send_message(tool_results)

    return state


# ── Helpers ────────────────────────────────────────────────────────────────────

def _has_tool_calls(response) -> bool:
    return any(
        p.function_call is not None
        for p in (response.parts or [])
    )


def _get_tool_calls(response):
    return [p.function_call for p in (response.parts or []) if p.function_call is not None]


def _extract_text(response) -> str:
    return response.text or ""


async def _dispatch(db: AsyncSession, call, state: dict) -> dict:
    """Route a Gemini function call to the correct tool function."""
    name = call.name
    args = dict(call.args) if call.args else {}

    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}

    result = await fn(db=db, **args)

    if name == "create_ticket" and "ticket_id" in result:
        state["ticket_id"] = result["ticket_id"]
    if name == "set_ticket_sentiment" and "sentiment_score" in result:
        state["sentiment"] = result["sentiment_score"]
    if name == "escalate_ticket":
        state["escalated"] = True

    return result
