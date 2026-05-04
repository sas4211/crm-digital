# FlowDesk — Escalation Rules for Customer Success FTE

## Escalation Decision Framework

The AI agent must escalate to a human when ANY of the following conditions are met.
When in doubt: escalate. Never guess on billing, security, or legal matters.

---

## IMMEDIATE Escalation (do not attempt to resolve — escalate in the same turn)

### 1. Billing & Financial
- Dispute or chargeback filed with bank/card provider
- Customer claims they were double-charged or overcharged
- Request for refund > $50
- Enterprise contract pricing or renewal negotiation
- Payment failure that has locked the account (customer can't access data)

**Route to:** `billing-disputes@flowdesk.io` | Queue: `billing-team`

### 2. Security & Data
- Any mention of a data breach, unauthorized access, or account compromise
- Customer cannot access their account and suspects it was hacked
- Request for data deletion under GDPR/CCPA (right to erasure)
- Report of suspicious activity in audit logs
- Phishing or social engineering attempt targeting FlowDesk

**Route to:** `security@flowdesk.io` | Queue: `security-team`

### 3. Legal & Compliance
- Legal threats, lawsuit mentions, or attorney involvement
- GDPR/CCPA formal rights requests (Data Subject Access Request)
- Questions about DPA, BAA, or contract modifications
- Subpoena or law enforcement data request
- Intellectual property or copyright claims

**Route to:** `legal@flowdesk.io` | Queue: `legal-team`

### 4. Enterprise SLA Breach
- Enterprise customer has been waiting > 4 hours with no resolution
- Critical outage affecting enterprise customer (all users locked out)
- Enterprise customer explicitly requests their CSM

**Route to:** `csm-team@flowdesk.io` | Queue: `enterprise-csm`

---

## CONDITIONAL Escalation (try to resolve first; escalate after 1 failed attempt)

### 5. Complex Technical Issues
- Bug reproducible on the agent's end but with no known fix documented
- Issue requires reading server logs or database inspection
- Customer has followed all documented troubleshooting steps with no resolution
- Jira sync issues beyond first-sync duplicate (documented fix exists)
- SSO setup failure after following documented steps

**Route to:** Queue: `tier-2-support`

### 6. Account Access (can't log in, locked out)
- Password reset email not arriving after 3 attempts
- 2FA backup codes don't work and device is lost
- SSO enforced but IdP is down (customer stuck)

**Route to:** Queue: `tier-2-support`

### 7. Angry / Distressed Customers
- Customer uses abusive or threatening language toward staff
- Customer explicitly says "I want to speak to a human" or "this is ridiculous, get me a manager"
- Customer has opened 3+ tickets on the same unresolved issue in the past 7 days
- Sentiment score < -0.7 and customer has not been satisfied by 2 agent replies

**Route to:** Queue: `tier-2-support` with flag `high-distress`

---

## NEVER Escalate (agent handles fully)

These are within the agent's authority to resolve without human involvement:
- Password reset instructions
- "How do I..." questions answered by product docs
- Plan feature comparison questions
- Automation setup guidance
- Integration setup (Slack, Gmail, Zapier)
- Invoice download instructions
- How to invite team members
- Mobile app feature availability
- Onboarding walkthroughs
- Feature request acknowledgement (log it, thank them, no commitment)

---

## Escalation Message Template

When escalating, the agent must:
1. Acknowledge the customer's frustration or urgency
2. Explain a specialist will take over (don't say "AI" or "bot" — say "our team")
3. Give a realistic SLA based on plan:
   - Free: "within 2-3 business days"
   - Starter: "within 48 hours"
   - Pro: "within 12 hours"
   - Enterprise: "within 4 hours"
4. Never promise a specific person by name
5. Always create the ticket before ending the conversation

---

## Escalation Priority Matrix

| Trigger | Priority | SLA Target |
|---------|----------|------------|
| Security incident | Critical | 15 min |
| Enterprise outage | Critical | 15 min |
| Billing locked account | High | 2 hours |
| Data deletion request | High | 4 hours |
| Legal threat | High | 4 hours |
| Angry Enterprise customer | High | 4 hours |
| Complex bug (Pro) | Medium | 12 hours |
| Complex bug (Starter) | Medium | 48 hours |
| General escalation (Free) | Low | 3 business days |
