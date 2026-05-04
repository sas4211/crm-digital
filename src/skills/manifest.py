"""
Agent Skills Manifest â€” Customer Success FTE

Reusable skill definitions that the agent (or any MCP client) can invoke.
Each skill declares: when to use, inputs, outputs, and the implementation
function from the prototype codebase.

These are declarative â€” the actual logic lives in src/core_loop_prototype.py
and src/conversation_state.py but is re-exported here for easy discovery.
"""

from dataclasses import dataclass, field
from typing import Callable, Any, Optional


# â”€â”€ Skill Definition â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass
class SkillInput:
    name: str
    type_hint: str
    description: str
    required: bool = True


@dataclass
class SkillOutput:
    name: str
    type_hint: str
    description: str


@dataclass
class AgentSkill:
    """A reusable agent capability."""
    skill_id: str
    display_name: str
    description: str
    when_to_use: str           # Trigger conditions
    inputs: list[SkillInput]
    outputs: list[SkillOutput]
    implementation: str        # Module path to the function
    priority: int = 0          # Higher = runs first in multi-skill chains


# â”€â”€ Skill Registry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

SKILLS: list[AgentSkill] = []


def register(**kwargs):
    """Decorator to register a skill definition."""
    def decorator(skill: AgentSkill) -> AgentSkill:
        SKILLS.append(skill)
        return skill
    return decorator


# â”€â”€ 1. Knowledge Retrieval â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

search_knowledge_base = register()(AgentSkill(
    skill_id="knowledge_retrieval",
    display_name="Knowledge Retrieval",
    description=(
        "Search the product knowledge base for relevant documentation. "
        "Returns structured KB entries with category, problem, and solution."
    ),
    when_to_use=(
        "Customer asks a product question, reports a bug, needs how-to guidance, "
        "or the agent doesn't have enough context to answer from memory. "
        "Always call this BEFORE composing a reply to ground responses in known solutions."
    ),
    inputs=[
        SkillInput(name="query", type_hint="str", description="The search term or customer question"),
    ],
    outputs=[
        SkillOutput(name="results", type_hint="list[KBResult]", description="Matching KB entries"),
    ],
    implementation="src.mcp_server.search_knowledge_base",
    priority=10,
))


# â”€â”€ 2. Sentiment Analysis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

sentiment_analysis = register()(AgentSkill(
    skill_id="sentiment_analysis",
    display_name="Sentiment Analysis",
    description=(
        "Score customer sentiment on a scale from -1.0 (very negative) to +1.0 "
        "(very positive). Also tracks sentiment trend across conversation turns."
    ),
    when_to_use=(
        "On EVERY incoming customer message. "
        "Determines whether to apply empathy-first responses, whether sentiment "
        "is worsening over time, and whether the interaction is going well."
    ),
    inputs=[
        SkillInput(name="text", type_hint="str", description="The customer's message body"),
    ],
    outputs=[
        SkillOutput(name="score", type_hint="float", description="Sentiment from -1.0 to +1.0"),
        SkillOutput(name="trend", type_hint="float", description="Direction: positive=improving, negative=worsening (requires session history)"),
    ],
    implementation="src.core_loop_prototype.estimate_sentiment",
    priority=20,  # Runs early, before classification
))


# â”€â”€ 3. Escalation Decision â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

escalation_decision = register()(AgentSkill(
    skill_id="escalation_decision",
    display_name="Escalation Decision",
    description=(
        "Determine whether a ticket should be escalated to a human agent. "
        "Checks for legal, security, and billing triggers as well as "
        "repeated-failure signals and extreme negative sentiment."
    ),
    when_to_use=(
        "On EVERY incoming message (runs before any other processing). "
        "Escalation keywords (legal, security, billing) trigger IMMEDIATE hand-off "
        "before the agent attempts to answer. "
        "Also called after generating a response if the agent cannot resolve the issue. "
        "Checks for SSO lockouts, GDPR/DSAR requests, refund demands, and threat language."
    ),
    inputs=[
        SkillInput(name="text", type_hint="str", description="The customer's message body"),
        SkillInput(name="sentiment", type_hint="float", description="Current sentiment score (optional, for escalation confidence)"),
        SkillInput(name="session_history", type_hint="Optional[ConversationSession]", description="Active session for trend analysis (optional)"),
    ],
    outputs=[
        SkillOutput(name="should_escalate", type_hint="bool", description="True if immediate escalation needed"),
        SkillOutput(name="queue", type_hint="str", description="Human queue name: legal-team, security-team, billing-team, enterprise-csm, tier-2-support"),
        SkillOutput(name="reason", type_hint="str", description="Why this ticket is being escalated"),
    ],
    implementation="src.core_loop_prototype.check_escalation",
    priority=30,  # Highest priority â€” runs first
))


# â”€â”€ 4. Channel Adaptation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

channel_adaptation = register()(AgentSkill(
    skill_id="channel_adaptation",
    display_name="Channel Adaptation",
    description=(
        "Format a response appropriately for the target channel. "
        "Applies channel-specific sign-offs, adjusts tone markers, "
        "and enforces length constraints."
    ),
    when_to_use=(
        "BEFORE sending any response. "
        "Email: professional, numbered steps, 'Best, Alex | FlowDesk Customer Success' sign-off. "
        "WhatsApp: casual, warm, max 1 emoji, 'â€” Alex, FlowDesk' brief sign-off. "
        "Web Form: direct, self-contained, NO sign-off, ticket ID shown separately."
    ),
    inputs=[
        SkillInput(name="body", type_hint="str", description="The draft response text"),
        SkillInput(name="channel", type_hint="str", description="Target channel: email, whatsapp, web_form"),
        SkillInput(name="customer_name", type_hint="str", description="Customer name for greeting"),
    ],
    outputs=[
        SkillOutput(name="formatted_body", type_hint="str", description="Response formatted for the channel"),
    ],
    implementation="src.core_loop_prototype._sign_off",
    priority=5,
))


# â”€â”€ 5. Customer Identification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

customer_identification = register()(AgentSkill(
    skill_id="customer_identification",
    display_name="Customer Identification",
    description=(
        "Identify the customer across channels using email as the primary key. "
        "Creates or retrieves the customer profile and merges channel history. "
        "Handles WhatsApp messages that may lack an email (uses phone as fallback)."
    ),
    when_to_use=(
        "On EVERY incoming message, before any other processing. "
        "Resolves the customer's unified identity and plan. "
        "WhatsApp: uses placeholder email if only phone is available. "
        "Web Form: email is captured from form fields. Email: extracted from header."
    ),
    inputs=[
        SkillInput(name="email", type_hint="str", description="Customer email address (primary key)"),
        SkillInput(name="name", type_hint="str", description="Customer display name"),
        SkillInput(name="phone", type_hint="str", description="Phone/WhatsApp number (fallback identifier)"),
        SkillInput(name="company", type_hint="str", description="Company name"),
        SkillInput(name="plan", type_hint="str", description="Subscription plan: free, starter, pro, enterprise"),
    ],
    outputs=[
        SkillOutput(name="customer_id", type_hint="str", description="Unified customer email"),
        SkillOutput(name="profile", type_hint="CustomerProfile", description="Full customer profile with stats"),
        SkillOutput(name="total_tickets", type_hint="int", description="Lifetime ticket count"),
        SkillOutput(name="resolutions", type_hint="int", description="Lifetime resolved count"),
    ],
    implementation="src.conversation_state.ConversationMemory.get_or_create_profile",
    priority=25,
))


# â”€â”€ 6. Conversation Memory â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

conversation_memory = register()(AgentSkill(
    skill_id="conversation_memory",
    display_name="Conversation Memory",
    description=(
        "Recall previous turns in the current conversation session. "
        "Enables the agent to understand follow-up questions, context "
        "references ('that solution didn't work'), and topic continuity. "
        "Also detects cross-channel switches (email -> WhatsApp)."
    ),
    when_to_use=(
        "After customer identification, to check if this is a new conversation "
        "or a continuation. Used to detect sentiment trends, topic accumulation, "
        "and whether the customer has switched channels mid-conversation."
    ),
    inputs=[
        SkillInput(name="customer_email", type_hint="str", description="Customer email for session lookup"),
    ],
    outputs=[
        SkillOutput(name="session", type_hint="Optional[ConversationSession]", description="Active session or None if new conversation"),
        SkillOutput(name="context_note", type_hint="str", description="Explanation for the agent: 'new_session' or channel switch notice"),
        SkillOutput(name="topic_history", type_hint="list[str]", description="Topics already discussed this session"),
    ],
    implementation="src.conversation_state.ConversationMemory.get_active_session",
    priority=15,
))


# â”€â”€ 7. Category Classification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

category_classification = register()(AgentSkill(
    skill_id="category_classification",
    display_name="Category Classification",
    description=(
        "Classify the customer's message into a support category. "
        "Used for routing replies to the right KB domain and for analytics."
    ),
    when_to_use=(
        "After escalation screening, before KB search. "
        "Determines which fallback template to use if the KB has no match."
    ),
    inputs=[
        SkillInput(name="text", type_hint="str", description="The customer's message body"),
    ],
    outputs=[
        SkillOutput(name="category", type_hint="str", description="One of: automations, billing, data, feature_request, integrations, login, mobile, views, general"),
    ],
    implementation="src.core_loop_prototype.classify_category",
    priority=12,
))


# â”€â”€ 8. Language Detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

language_detection = register()(AgentSkill(
    skill_id="language_detection",
    display_name="Language Detection",
    description=(
        "Detect the customer's language so the agent responds in the same language. "
        "Currently supports English (default), Spanish, French, and Portuguese."
    ),
    when_to_use=(
        "On EVERY incoming message, as the very first processing step. "
        "Sets the response language for all downstream reply generation."
    ),
    inputs=[
        SkillInput(name="text", type_hint="str", description="The customer's message body"),
    ],
    outputs=[
        SkillOutput(name="language", type_hint="str", description="Detected language name (English, Spanish, French, Portuguese). English is the fallback."),
    ],
    implementation="src.core_loop_prototype.detect_language",
    priority=40,  # Runs first
))


def get_skill(skill_id: str) -> Optional[AgentSkill]:
    """Look up a skill by ID."""
    for s in SKILLS:
        if s.skill_id == skill_id:
            return s
    return None


def list_skills() -> list[AgentSkill]:
    """All registered skills, sorted by priority (highest first)."""
    return sorted(SKILLS, key=lambda s: s.priority, reverse=True)
