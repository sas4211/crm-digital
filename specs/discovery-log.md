# Discovery Log — Exercise 1.1: Initial Exploration

**Agent:** Claude Code (Director mode)
**Date:** 2026-04-03
**Input:** 55 sample tickets across Gmail, WhatsApp, Web Form + full context dossier
**Method:** Pattern analysis across channel, category, priority, sentiment, and escalation signals

---

## 1. Ticket Volume by Channel

| Channel | Count | % of total |
|---------|-------|------------|
| Email | 20 | 36% |
| WhatsApp | 19 | 35% |
| Web Form | 16 | 29% |

**Finding:** Volume is roughly balanced across channels. No channel dominates, meaning the agent must be equally proficient at all three. However, each channel has a very distinct interaction _style_ (see Section 3).

---

## 2. Issue Category Distribution

| Category | Count | Most Common Channel |
|----------|-------|-------------------|
| How-to / Feature questions | 14 | WhatsApp |
| Billing | 10 | Email |
| Bug reports | 7 | Email / Web Form |
| Integration issues | 5 | Email |
| Login / Access | 4 | Web Form / Email |
| Security | 3 | Email |
| Legal / Compliance | 3 | Email |
| Feature requests | 3 | WhatsApp |
| Cancellation | 1 | Email |
| Other | 5 | Mixed |

**Finding:** How-to questions (26%) are the highest volume — the agent must have deep product doc retrieval. Billing issues (18%) are second — many require escalation. Security + Legal (11% combined) are low volume but always critical escalations.

---

## 3. Channel-Specific Patterns (Critical Discovery)

### Email
- **Longer, more formal.** Customers write in paragraphs with signature blocks.
- **Higher stakes.** Email tickets skew toward billing disputes, legal threats, security incidents, and enterprise concerns.
- **Attachments referenced** (screenshot, PDF, contract) — agent should acknowledge even if it can't process files.
- **Reply-threading matters.** Customers expect the reply to land in the same email thread.
- **Multi-sentence grievances.** Angry customers write long emails. Agent must read all the way through before classifying.
- **Language diversity higher.** Found: English, French, German, Swedish, Arabic context implied.

### WhatsApp
- **Conversational, lowercase, abbreviated.** "can i", "hey!!", "quick q"
- **Single-question inquiries.** Rarely more than 1-2 sentences. Often just one question.
- **Emoji present.** "my eyes are dying 😭" — agent should match casual warmth, 1 emoji max.
- **Multilingual.** Found French (t014, t023) and implied Spanish. Agent must detect language and respond in kind.
- **Faster expectations.** WhatsApp customers expect near-instant replies. Escalation messages must be brief.
- **Lower stakes by default** — but t048 (account compromise) came via WhatsApp, proving channel ≠ severity.
- **No formal signature expected.** End with "— Alex, FlowDesk" only.

### Web Form
- **Structured and complete.** Customers fill in all fields (name, email, subject, message). Less context-guessing needed.
- **Mid-length.** More detail than WhatsApp, less formal than email.
- **Response shown inline.** The reply must be self-contained — customer reads it on-screen immediately.
- **Higher "how-to" density.** Customers seem to use the form when they can't find the answer themselves.
- **No follow-up thread.** If the form reply doesn't solve it, they'll open a new ticket — agent should be thorough on first reply.

---

## 4. Escalation Signal Analysis

### Escalation Rate
- **24 out of 55 tickets (44%) require escalation** — much higher than initially assumed.
- This means the agent's most important skill after answering questions is **recognising when NOT to answer**.

### Escalation Trigger Patterns

| Trigger Word/Phrase | Example | Escalate To |
|--------------------|---------|-------------|
| "attorney", "legal", "court", "notice" | t018 | legal-team |
| "GDPR", "DSAR", "data deletion" | t009 | legal-team |
| "breach", "unauthorized access", "hacked" | t004, t048 | security-team |
| "double charged", "refund", "overcharged" | t006 | billing-team |
| "third time", "still not fixed", "unacceptable" | t021 | tier-2 (high-distress) |
| "I want to speak to a human" | (implicit in t021) | tier-2 |
| "CSM", "contract renewal", "annual discount" | t039 | enterprise-csm |
| "SOC 2", "DPA", "BAA" | t022 | legal-team |
| 2FA lost + backup codes failed | t027 | tier-2 |
| 40+ users locked out | t052 | tier-2 (critical) |

**Hidden requirement discovered:** The agent must perform **keyword scanning before attempting to answer**. Several tickets _look_ like normal questions but contain legal or security triggers buried in the message body (e.g. t018 opens like a complaint but is a legal notice; t009 looks like a product question but is a formal GDPR request).

---

## 5. Sentiment Distribution

| Sentiment | Count | Indicators |
|-----------|-------|------------|
| Positive | 8 | "love flowdesk", "quick q", thanks, emojis |
| Neutral | 30 | Plain questions, technical requests |
| Negative | 12 | Frustration, urgency words, ALL CAPS, legal threats |
| Critical (abusive/threatening) | 5 | t018, t021, t004, t027, t052 |

**Key insight:** Negative sentiment customers need **empathy-first responses**. The agent must detect emotional tone before choosing a response template. A negative-sentiment customer who receives a robotic step-list will escalate to a worse outcome.

---

## 6. Multilingual Requirements (Hidden Requirement)

Found 4 non-English tickets:
- **t014** — Spanish: "cuando sale la integración con Microsoft Teams?"
- **t023** — French: "je veux upgrader vers starter mais j'ai une erreur"
- **t036** — French with English expectation
- **t051** — Portuguese: "Olá... Obrigada"

**Requirement crystallised:** The agent must detect the customer's language (from message body) and respond **in the same language**. English is the fallback if detection fails.

Gemini 1.5 Pro natively supports 40+ languages — no translation API needed.

---

## 7. Plan-Tier Patterns

| Plan | Behaviour pattern |
|------|-----------------|
| Free | Questions about limits, upgrade friction (Firefox bug), simpler issues |
| Starter | Most common tier. Mix of how-to + billing + occasional bugs |
| Pro | Integration + automation + Jira issues. More technical depth expected |
| Enterprise | Security, compliance, SSO, contract negotiation — nearly always escalate |

**Insight:** The agent should check the customer's plan before crafting a reply, as the answer often depends on it ("automations on Free = no, on Pro = unlimited").

---

## 8. Knowledge Base Seed Categories

From the 55 tickets, the following KB categories emerge:

1. `login-access` — password reset, 2FA, SSO lockout
2. `billing-plans` — upgrades, limits, invoices, refunds
3. `automations` — setup, limits, duplicate rules
4. `integrations-slack` — connection, notifications
5. `integrations-jira` — first-sync duplicate fix
6. `integrations-github` — GitHub Enterprise webhook
7. `integrations-zapier` — plan requirements
8. `how-to-basics` — archive project, delete project, assign tasks
9. `how-to-views` — Timeline (Pro+), Calendar, My Work
10. `mobile-app` — known limitations, crashes
11. `security-incidents` — unauthorized access handling
12. `data-export-import` — CSV, Google Sheets
13. `feature-requests` — dark mode, Teams, recurring tasks

---

## 9. Crystallised Requirements (Not in Original Brief)

These requirements were **not explicit** in the hackathon brief but are essential based on ticket analysis:

| # | Hidden Requirement | Evidence |
|---|--------------------|---------|
| R1 | Respond in customer's language | t014, t023, t051 |
| R2 | Keyword-scan for legal/security before answering | t018, t009 — would fool a naive agent |
| R3 | Check plan before answering feature questions | t010, t031, t050 — answer depends on plan |
| R4 | Empathy-first for negative sentiment tickets | t021, t004, t027 |
| R5 | Cross-channel consistency — same quality regardless of channel | t048 (security via WhatsApp) |
| R6 | Handle incomplete customer info (WhatsApp lacks email) | All WhatsApp tickets use placeholder email |
| R7 | Detect "repeat ticket" signals and escalate | t021 mentions 3 prior tickets |
| R8 | Temp workaround for SSO lockout (disable enforcement) | t052 — 40 users blocked |
| R9 | Never confirm or deny features on the roadmap with dates | t014, t026 — Teams, dark mode |
| R10 | Attachment acknowledgement even though agent can't read files | t001 (implied PDF) |

---

## 10. Agent Personality Requirements (from brand-voice.md)

The agent name is **Alex**. Key behavioural rules distilled:

- Never say "I'm an AI" or "as a language model"
- Always use the customer's first name once
- Lead with resolution, then explanation
- WhatsApp: casual, brief, max 1 emoji
- Email: professional, numbered steps, sign off "Best, Alex | FlowDesk Customer Success"
- Web Form: no sign-off, include ticket ID
- Never make up features or commit to timelines

---

## 11. Core Interaction Loop (Prototyped)

Based on exploration, the agent's core loop for every ticket is:

```
RECEIVE message
    │
    ├─► STEP 1: Detect language
    ├─► STEP 2: Identify customer (email/phone → DB lookup)
    ├─► STEP 3: Assess sentiment score
    ├─► STEP 4: KEYWORD SCAN — legal/security triggers?
    │           YES → IMMEDIATE ESCALATE (do not pass Go)
    │           NO → continue
    ├─► STEP 5: Classify category
    ├─► STEP 6: Check customer's plan (affects answer)
    ├─► STEP 7: Search knowledge base
    ├─► STEP 8: Is this within agent authority?
    │           NO → CONDITIONAL ESCALATE
    │           YES → compose reply in correct language + tone
    ├─► STEP 9: Log reply to ticket
    ├─► STEP 10: Send via channel
    └─► STEP 11: If resolved → save to KB + mark ticket resolved
```

---

## 12. Test Cases Discovered (→ tests/)

The following scenarios should be in the test suite (written to `tests/` in Exercise 1.2):

| Test ID | Scenario | Expected Outcome |
|---------|----------|-----------------|
| TC-01 | Legal threat in email body | Escalate immediately, no resolution attempt |
| TC-02 | WhatsApp message in Spanish | Reply in Spanish |
| TC-03 | Free plan asking about automations | Explain plan limit, offer upgrade |
| TC-04 | Known Jira first-sync bug | Provide documented fix |
| TC-05 | Angry customer (3rd ticket) | Empathy + immediate escalation |
| TC-06 | Password reset not working | Steps → escalate if 3 attempts fail |
| TC-07 | Double charge claim | Escalate, do not attempt refund |
| TC-08 | Enterprise SSO lockout (40 users) | Temp workaround + escalate |
| TC-09 | GDPR data deletion request | Escalate to legal, do not process |
| TC-10 | WhatsApp emoji-heavy message | Match casual tone, max 1 emoji back |
| TC-11 | Feature request (dark mode) | Acknowledge, no roadmap commitment |
| TC-12 | Security incident via WhatsApp | Same critical response as email |
| TC-13 | Pro customer asking about Gantt | Confirm available, walk through |
| TC-14 | Neutral technical question | Direct answer, no unnecessary empathy |
| TC-15 | Multilingual (French web form) | Detect language, respond in French |

---

*Discovery log generated: 2026-04-03 | Next: Exercise 1.2 — Prototype the Core Loop*

---

## Appendix — Exercise 1.2: Core Loop Prototype

**Status:** Complete
**Files:** `src/core_loop_prototype.py`, `tests/test_core_loop.py`
**Tests:** 45/45 passing

Key decisions:
- Rules-based prototype (no Gemini API required) enables immediate iteration
- Keyword scanning MUST run before any answering attempt (validates R2 from discovery)
- Category ordering matters: "automations" must match before "billing" catches "plan"
- SSO lockout needs specific pattern for mass-scale incidents

---

## Appendix — Exercise 1.3: Conversation Memory

**Status:** Complete
**Files:** `src/conversation_state.py`, `tests/test_conversation_state.py`
**Tests:** 26/26 passing (total including 1.2: 71)

Key decisions:
- Email is the single source of truth for customer identity
- Session timeout (1 hour) auto-archives to history
- Sentiment trend (first-half vs second-half) enables worsening detection
- Channel history tracks every message's channel for cross-switch detection

---

## Appendix — Exercise 1.4: MCP Server + Skills

**Status:** Complete
**Files:** `src/mcp_server.py`, `src/skills/manifest.py`, `specs/customer-success-fte-spec.md`
**Tests:** 60 new MCP + Skills tests passing (131 total across all suites)

### Deliverables Checklist

- [x] Working prototype that handles customer queries from any channel
- [x] Discovery log documenting requirements found during exploration
- [x] MCP server with 8 tools exposed (exceeds 5+ requirement)
- [x] Agent skills defined and tested (8 skills, 36 tests)
- [x] Edge cases documented with handling strategies (see spec.md section "Edge Cases Documented")
- [x] Escalation rules crystallized from testing (see spec.md section "Escalation Rules")
- [x] Channel-specific response templates discovered (see spec.md section "Channel Responses")
- [x] Performance baseline established (131/131 tests, <0.01s processing)
