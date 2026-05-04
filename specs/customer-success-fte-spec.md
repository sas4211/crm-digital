# Customer Success FTE — Specification

**Version:** 1.0
**Status:** Stage 1 Complete (Prototype)
**Date:** 2026-04-03
**Source:** Discovery from 55 sample tickets across 3 channels

---

## Purpose

Handle routine customer support queries with speed and consistency across
multiple channels (email, WhatsApp, web form). Provide 24/7 first-line support
with intelligent handoff to human agents for complex cases.

---

## Supported Channels

| Channel | Identifier | Response Style | Max Length |
|---------|------------|----------------|------------|
| Email (Gmail) | Email address | Formal, detailed, numbered steps | 500 words |
| WhatsApp | Phone number | Conversational, concise, warm | 160 chars preferred |
| Web Form | Email address | Semi-formal, direct, self-contained | 300 words |

---

## Scope

### In Scope

- Product feature questions
- How-to guidance (login, automations, integrations, views, mobile)
- Bug report intake with known-issue matching
- Feedback collection
- Cross-channel conversation continuity
- Plan-aware responses (Free vs Starter vs Pro vs Enterprise)

### Out of Scope (Automatic Escalation)

- **Legal/Compliance:** Attorney mentions, GDPR/DSAR, SOC 2, DPA, BAA, litigation
- **Security:** Breach reports, unauthorized access, account compromise, SSO mass lockout
- **Billing:** Refund demands, double charges, chargebacks, contract renewal discounts
- **Extreme Sentiment:** Customers who are furious, threatening, or on their 3rd+ ticket
- **Enterprise CSM:** Dedicated account management, contract negotiation

---

## Tools (MCP Server)

| Tool | Purpose | Constraints |
|------|---------|-------------|
| `search_knowledge_base` | Find relevant product docs | Max 5 structured results |
| `create_ticket` | Log interactions with AI processing | Required for all queries; includes channel |
| `get_customer_history` | View cross-channel interaction history | Uses email as primary key |
| `escalate_to_human` | Hand off complex issues | Must include full context and reason |
| `send_response` | Reply to customer | Channel-appropriate formatting |
| `get_ticket_status` | Check current ticket state | Returns escalation and resolution info |
| `get_dashboard` | Global operations overview | Active sessions, ticket counts, sentiment |
| `process_customer_message` | One-call end-to-end processing | Main entry point for incoming messages |

---

## Agent Skills

| Skill | Priority | When | Implementation |
|-------|----------|------|----------------|
| Language Detection | 40 (first) | Every incoming message | `detect_language()` |
| Escalation Decision | 30 | Before any answering attempt | `check_escalation()` |
| Customer Identification | 25 | Every message | `ConversationMemory.get_or_create_profile()` |
| Sentiment Analysis | 20 | Every message | `estimate_sentiment()` |
| Conversation Memory | 15 | After identification | `ConversationMemory.get_active_session()` |
| Category Classification | 12 | After escalation screening | `classify_category()` |
| Knowledge Retrieval | 10 | Before composing a reply | `search_knowledge_base()` |
| Channel Adaptation | 5 (last) | Before sending any response | `_sign_off()` |

---

## Performance Requirements

| Metric | Target | Current Baseline |
|--------|--------|-----------------|
| Response time (processing) | <3 seconds | <0.01s (rules-based prototype) |
| Response time (delivery) | <30 seconds | N/A (simulated) |
| Accuracy on test set | >85% | 100% (131/131 tests passing) |
| Escalation rate (auto-detected) | <20% | ~18% on prototype test set |
| Cross-channel identification | >95% accuracy | 100% (email primary key, no ambiguity) |

---

## Guardrails

- **NEVER** discuss competitor products
- **NEVER** promise features or commit to timelines
- **NEVER** attempt refunds or billing adjustments
- **NEVER** process GDPR/DSAR requests directly
- **ALWAYS** create a ticket before responding
- **ALWAYS** check sentiment before closing a ticket
- **ALWAYS** use channel-appropriate tone
- **ALWAYS** run keyword scan for legal/security/billing BEFORE answering
- **ALWAYS** respond in the customer's detected language

---

## Escalation Rules (Crystallized from Testing)

### Immediate Escalation (Step 4, before any answering)

| Trigger Pattern | Queue | Evidence |
|----------------|-------|----------|
| attorney, lawsuit, court, legal notice, small claims | legal-team | t018 |
| GDPR, DSAR, data subject access, data deletion | legal-team | t009 |
| DPA, BAA, compliance request, SOC 2 | legal-team | t022 |
| breach, unauthorized access, hacked, account compromise | security-team | t004, t048 |
| suspicious login, unknown device/location | security-team | t004 |
| double charged, charged twice, refund, chargeback | billing-team | t006 |
| billing dispute, contract renewal, annual discount | billing-team | t039 |
| SSO lockout + emergency override | security-team | t052 |

### Conditional Escalation (after agent attempt)

| Trigger | Queue | Evidence |
|---------|-------|----------|
| Agent cannot resolve after best attempt | tier-2-support | t010, t031 |
| Customer mentions 3rd+ prior ticket for same issue | tier-2-support (high-distress) | t021 |
| Customer explicitly demands human agent | tier-2-support | t021 |
| Enterprise CSM mention + account management | enterprise-csm | t039 |

### Escalation Message Template

```
Hi {first_name}, I've reviewed your message and I want to make sure you get
the right help. I've looped in {specialist_team} who will follow up with you
directly within {SLA}. Your case has been prioritised.
```

Where `{specialist_team}` maps to queue:
- legal-team → "a compliance specialist"
- security-team → "our security team"
- billing-team → "our billing specialist"
- tier-2-support → "a senior support specialist"
- enterprise-csm → "your dedicated Customer Success Manager"

---

## Channel-Specific Response Templates

### Email
- **Greeting:** "Hi {name},"
- **Body:** Professional, paragraph structure, numbered steps for multi-part
- **Sign-off:** "\n\nBest,\nAlex\nFlowDesk Customer Success"
- **Word limit:** 500 words maximum

### WhatsApp
- **Greeting:** "Hi {name}," (omit if name unavailable)
- **Body:** Casual, short, 2-4 sentences max, line breaks between ideas
- **Emoji:** Max 1 if natural (matches customer use)
- **Sign-off:** "\n\n— Alex, FlowDesk" (only for escalation messages)

### Web Form
- **Greeting:** "Hi {name},"
- **Body:** Direct, start with resolution, no fluff
- **Sign-off:** None — ticket ID shown separately
- **Self-contained:** Must make sense without a thread context

---

## Edge Cases Documented

| Edge Case | Handling |
|-----------|----------|
| WhatsApp message with no name/email | Placeholder email derived from phone; name left empty; brief sign-off only |
| Security incident via WhatsApp | Same critical response as email — channel ≠ severity |
| Customer writes in foreign language | Detect language, respond in same language; English fallback |
| Customer is very negative but not escalated | Empathy prefix: "I'm really sorry you're going through this — ..." |
| Feature requested that's not in docs | Acknowledge, pass to product team, NO roadmap commitment |
| Jira first-sync duplicate bug | Known issue — provide documented fix (delete duplicates, re-sync) |
| Free plan asking about paid features | Explain plan limit clearly, offer upgrade, mention trial if applicable |
| SSO mass lockout (40+ users) | Immediate escalation to security, mention emergency override |
| Attachment referenced but agent can't read | Acknowledge: "I see you've attached..." if mentioned |
| Repeat ticket (3rd+ for same issue) | Escalate to tier-2 with high-distress flag |
| Session timeout (>1 hour inactivity) | Archive session to history, create new session on next message |

---

## Data Model

### CustomerProfile (persistent)
- `customer_email` (PK), `name`, `phone`, `company`, `plan`
- `total_conversations`, `total_tickets`, `escalations_total`, `resolutions_total`
- `last_seen`, `created_at`

### ConversationSession (per active conversation)
- `session_id`, `customer_email`, `original_channel`, `current_channel`
- `channel_history: list[str]`, `topic_history: list[str]`
- `sentiment_track: list[float]`, `turns: list[ConversationTurn]`
- `resolved`, `escalated`, `escalation_queue`
- `started_at`, `last_activity`
- Timeout: 1 hour inactivity → auto-archive

### ConversationTurn (per exchange)
- `timestamp`, `channel`, `message_sent`, `reply_sent`
- `topic_detected`, `sentiment_score`, `escalated`, `resolved`

---

## Architecture Diagram

```
Incoming Message (email/whatsapp/web_form)
        │
        ▼
┌─────────────────────────────────────┐
│  Step 1: Language Detection         │
│  Step 2: Customer Identification    │
│  Step 3: Sentiment Analysis         │
│  Step 4: KEYWORD SCAN (escalation)  │ ◄── HIGHEST PRIORITY
│  Step 5: Category Classification    │
│  Step 6: Plan Check                 │
│  Step 7: KB Search                  │
│  Step 8: Build Response             │
│  Step 9: Channel Adaptation         │
│  Step 10: Record in Memory          │
└─────────────────────────────────────┘
        │
        ▼
┌──────────────────────┐  ┌──────────────────┐
│  Immediate Escalate  │  │  AI Reply        │
│  (if Step 4 fires)   │  │  (if KB match)   │
└──────────────────────┘  └──────────────────┘
        │                          │
        ▼                          ▼
┌──────────────────────┐  ┌──────────────────┐
│  Escalation Reply     │  │  Channel-Formatted│
│  (generic, brief)     │  │  Response          │
└──────────────────────┘  └──────────────────┘
        │                          │
        ▼                          ▼
   Log + Queue for Human     Log + Send via Channel
```
