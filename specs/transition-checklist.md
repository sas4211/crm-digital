# Transition Checklist: General → Custom Agent

## 1. Discovered Requirements

- [ ] Multi-channel message ingestion: Gmail (pub/sub), WhatsApp (Twilio webhook), Web form (REST API)
- [ ] Customer lookup by email, phone, or customer ID across all channels
- [ ] Interaction logging persisted to PostgreSQL for audit trails
- [ ] LLM responses must be channeled through Claude API (not returned bare)
- [ ] Response formatting differs per channel (HTML email, WhatsApp markdown, JSON web)
- [ ] Escalation to human agents on billing issues, complaints, or unclear intents
- [ ] NotebookLM integration for customer research and AI-generated insights
- [ ] Kafka for message queue between channel handlers and agent workers
- [ ] Kubernetes deployment with liveness/readiness probes
- [ ] Metrics collection on response time, escalation rate, and channel throughput

## 2. Working Prompts

### System Prompt That Worked:

```
You are a Customer Success Agent for a CRM platform. Your role is to:
1. Greet customers warmly and understand their needs
2. Answer questions about their account, deals, and past interactions
3. Log interactions and update customer records appropriately
4. Suggest products, next steps, or follow-ups based on customer context
5. Escalate issues to human agents when needed
Always be professional, empathetic, and solution-oriented.
```

### Agent System Template That Worked:

```
You are {agent_name}, an AI customer success agent for {company_name}.
Context includes customer name, ID, channel, deal count, last interaction.
Must acknowledge customer by name, reference history, be concise, never fabricate data.
```

## 3. Edge Cases Found

| Edge Case | How It's Handled | Test Case Needed |
|---|---|---|
| Unknown customer (no match by email/phone) | Log to DB, skip agent processing | Yes |
| Empty/whitespace message | Skip processing, return status="skipped" | Yes |
| Malformed Kafka message | Log warning, skip, don't crash | Yes |
| Customer not found in DB | Return success=False with "Customer not found" | Yes |
| Escalation trigger | Build escalation payload with priority level | Yes |
| Database connection dropped | Pool reconnect on next acquire attempt | Yes |

## 4. Response Patterns

- **Email**: HTML-formatted with branded signature, max 640px width
- **WhatsApp**: Plain text with minimal markdown (*bold*, _italic_)
- **Web**: JSON with content, timestamp, channel, success fields

## 5. Escalation Rules (Finalized)

When does escalation trigger:
- Billing dispute or complaint mentioned
- Customer explicitly requests a human representative
- Agent is uncertain — no matching data found
- Repeated failed interactions (configurable threshold)

## 6. Performance Baseline

From your prototype testing:
- Average response time: TBD seconds (wire to Claude API)
- Accuracy on test set: TBD% (depends on LLM evaluation)
- Escalation rate: TBD% (monitored via metrics_collector)
