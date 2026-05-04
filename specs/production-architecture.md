# Production Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CUSTOMER CHANNELS                                  │
│                                                                             │
│   ┌──────────┐       ┌──────────────┐       ┌─────────────┐               │
│   │  Gmail   │       │   WhatsApp   │       │  Web Form   │               │
│   │  Inbox   │       │   Business   │       │  (Next.js)  │               │
│   └────┬─────┘       └──────┬───────┘       └──────┬──────┘               │
│        │                    │                       │                      │
└────────┼────────────────────┼───────────────────────┼──────────────────────┘
         │                    │                       │
         │                    │                       │
┌────────┼────────────────────┼───────────────────────┼──────────────────────┐
│        │                    │                       │                      │
│        ▼                    ▼                       ▼                      │
│  ┌──────────┐         ┌──────────┐          ┌──────────┐                 │
│  │  Gmail   │         │ Twilio   │          │  Web     │                 │
│  │ Pub/Sub  │         │ Webhook  │          │ Webhook  │                 │
│  │ Webhook  │         │          │          │          │                 │
│  └────┬─────┘         └────┬─────┘          └────┬─────┘                 │
│       │                    │                      │                       │
│       └────────────────────┼──────────────────────┘                       │
│                            │                                              │
│                            ▼                                              │
│              ┌──────────────────────────────────┐                         │
│              │   FASTAPI WEBHOOK HANDLER        │                         │
│              │   (Kubernetes Deployment)        │                         │
│              │   - POST /webhooks/gmail         │                         │
│              │   - POST /webhooks/whatsapp      │                         │
│              │   - POST /webhooks/web-form      │                         │
│              │   Replicas: 3-10 (HPA)           │                         │
│              └──────────┬───────────────────────┘                         │
│                         │                                                 │
│                         ▼                                                 │
│              ┌──────────────────────────────────┐                         │
│              │   AGENT ORCHESTRATOR              │                         │
│              │   src/agent/agent.py              │                         │
│              │   - run_agent(message)            │                         │
│              │   - Async task queue              │                         │
│              └──────────┬───────────────────────┘                         │
│                         │                                                 │
│        ┌────────────────┼────────────────┐                               │
│        │                │                │                               │
│        ▼                ▼                ▼                               │
│  ┌──────────┐   ┌──────────────┐  ┌──────────────┐                      │
│  │   Core   │   │   Gemini     │  │  Tool        │                      │
│  │   Loop   │   │   Function   │  │  Executor    │                      │
│  │          │   │   Calling    │  │              │                      │
│  └────┬─────┘   └──────┬───────┘  └──────┬───────┘                      │
│       │                │                  │                              │
│       └────────────────┼──────────────────┘                              │
│                        │                                                 │
│                        ▼                                                 │
│         ┌──────────────────────────────────────────┐                     │
│         │         GEMINI 1.5 PRO                   │                     │
│         │   - Language detection                   │                     │
│         │   - Sentiment analysis                   │                     │
│         │   - Category classification              │                     │
│         │   - Response generation                  │                     │
│         │   - Function tool calls                  │                     │
│         └──────────┬───────────────────────────────┘                     │
│                    │                                                     │
│                    ▼                                                     │
│         ┌──────────────────────────────────────────┐                     │
│         │         TOOL LAYER (8 Tools)             │                     │
│         │   src/agent/tools.py                     │                     │
│         │   ┌──────────────────────────────────┐   │                     │
│         │   │ 1. search_knowledge_base()       │   │                     │
│         │   │ 2. create_ticket()               │   │                     │
│         │   │ 3. get_customer_history()        │   │                     │
│         │   │ 4. escalate_to_human()           │   │                     │
│         │   │ 5. send_response()               │   │                     │
│         │   │ 6. get_ticket_status()           │   │                     │
│         │   │ 7. get_dashboard()               │   │                     │
│         │   │ 8. NotebookLM enrichment         │   │                     │
│         │   └──────────────────────────────────┘   │                     │
│         └──────────┬───────────────────────────────┘                     │
│                    │                                                     │
│  INFRASTRUCTURE LAYER                                                    │
└────────────────────┼─────────────────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
   ┌──────────┐ ┌─────────┐ ┌─────────┐
   │PostgreSQL│ │  Redis  │ │  Kafka  │
   │  Cloud   │ │  Cache  │ │ Events  │
   │   SQL    │ │         │ │         │
   └────┬─────┘ └────┬────┘ └────┬────┘
        │            │           │
        │            │           │
        ▼            ▼           ▼
   ┌─────────────────────────────────┐
   │    PERSISTENCE & EVENTS         │
   │  - customers table              │
   │  - tickets table                │
   │  - messages table               │
   │  - knowledge_base table         │
   │  - Session cache (1h TTL)       │
   │  - Event stream (escalations)   │
   └─────────────────────────────────┘
                     │
                     ▼
   ┌─────────────────────────────────┐
   │    OBSERVABILITY STACK          │
   │  - Prometheus (metrics)         │
   │  - Grafana (dashboards)         │
   │  - Jaeger (tracing)             │
   │  - Kafka → BigQuery (analytics) │
   │  - Sentry (errors)              │
   └─────────────────────────────────┘
                     │
                     ▼
   ┌─────────────────────────────────┐
   │    ENRICHMENT LAYER             │
   │  - NotebookLM (async worker)    │
   │  - Claude API (CRM notes)       │
   │  - Gemini Gems (personas)       │
   │  - Daily reports (CronJob)      │
   └─────────────────────────────────┘
```

---

## Data Flow: Email Ticket → Resolution

```
1. Customer sends email to support@flowdesk.io
         │
         ▼
2. Gmail Pub/Sub push notification
         │
         ▼
3. FastAPI webhook receives POST /webhooks/gmail
         │
         ▼
4. Parse email, extract sender, body, thread_id
         │
         ▼
5. Call run_agent(customer_email, message_body, channel="email")
         │
         ├──► Check Redis cache for active session
         │
         ├──► DB query: get_or_create_customer()
         │
         └──► DB query: find open ticket or create new
         │
         ▼
6. Gemini function calling loop
         │
         ├──► Tool: detect_language() → "English"
         ├──► Tool: estimate_sentiment() → -0.3 (slightly negative)
         ├──► Tool: check_escalation() → False (no triggers)
         ├──► Tool: classify_category() → "billing"
         ├──► Tool: search_knowledge_base(query="billing") → 3 results
         └──► Gemini generates reply with KB context
         │
         ▼
7. Apply channel formatting (email sign-off)
         │
         ▼
8. Insert message to DB (role="agent", body=reply)
         │
         ▼
9. Call Gmail API: send reply in thread
         │
         ├──► Retry logic (3 attempts)
         └──► Update ticket status to "waiting_customer"
         │
         ▼
10. Emit Kafka event: ticket.reply.sent
         │
         ▼
11. Update Prometheus metrics: tickets_total{channel="email", status="resolved"}
         │
         ▼
12. Return 200 OK to webhook
```

---

## Escalation Flow: Security Incident

```
1. Customer WhatsApp message: "My account was hacked, someone logged in from Russia"
         │
         ▼
2. Twilio webhook POST /webhooks/whatsapp
         │
         ▼
3. run_agent(channel="whatsapp", message_body=...)
         │
         ▼
4. Gemini: detect_language() → "English"
   Gemini: estimate_sentiment() → -0.8 (very negative)
   Gemini: check_escalation() → True
         │
         ▼ Escalation trigger: "hacked" matches security-team pattern
         │
5. Gemini calls tool: escalate_to_human(
         queue="security-team",
         reason="account compromise",
         priority="critical"
   )
         │
         ▼
6. DB: update ticket set escalated_to="security-team", priority="critical"
         │
         ▼
7. Send escalation message via WhatsApp:
   "Hi {name}, I've reviewed your message and looped in our security team..."
         │
         ▼
8. Emit Kafka event: ticket.escalated
         │
         ▼
9. Kafka consumer → Slack notification to #security-alerts channel
         │
         ▼
10. Security team receives alert, claims ticket in dashboard
         │
         ▼
11. Human agent reviews history, contacts customer within 2 hours (SLA)
```

---

## NotebookLM Enrichment Flow (Async)

```
1. Customer record created for "Acme Corp" (Enterprise plan)
         │
         ▼
2. Async worker picks up enrichment task from queue
         │
         ▼
3. Call stitch.pipeline.enrich_customer(
         customer_name="Acme Corp",
         website="https://acme.com",
         files=["./contracts/acme-msa.pdf"]
   )
         │
         ├──► NotebookLM: create notebook "CRM: Acme Corp"
         ├──► NotebookLM: add source (website)
         ├──► NotebookLM: add source (PDF contract)
         ├──► NotebookLM: generate briefing doc
         ├──► NotebookLM: ask "What are their pain points?"
         │
         ▼
4. Run Gemini Gems on brief
         │
         ├──► DealAnalystGem() → deal_score, risk_level, next_actions
         ├──► CustomerResearcherGem() → buying_signals, competitors
         └──► ObjectionHandlerGem() → responses to common objections
         │
         ▼
5. Claude API: Write concise CRM note from Gem outputs
         │
         ▼
6. DB: Update customer record with enrichment data
   - ai_deal_score: 7.5/10
   - ai_risk_level: "medium"
   - ai_next_actions: ["Schedule demo", "Send ROI calculator", "Intro to CSM"]
         │
         ▼
7. Emit Kafka event: customer.enriched
         │
         ▼
8. CRM UI displays enriched customer profile with AI insights
```

---

## Monitoring & Alerting

### Prometheus Metrics (Key Indicators)

```
# Throughput
tickets_total{channel, status, category}       # Counter
messages_total{role, channel}                  # Counter

# Latency
response_time_seconds{channel, p50, p90, p99}  # Histogram
gemini_api_duration_seconds{p50, p90, p99}     # Histogram

# Errors
escalation_rate{queue}                         # Gauge (target: 15-20%)
false_escalation_rate                          # Gauge (target: <2%)
gemini_api_errors_total                        # Counter
db_connection_errors_total                     # Counter

# Quality
customer_satisfaction_score{channel}           # Gauge (target: >4.0/5.0)
first_contact_resolution_rate                  # Gauge (target: >70%)
average_sentiment{channel}                     # Gauge

# Infrastructure
db_connection_pool_active                      # Gauge
db_connection_pool_idle                        # Gauge
redis_cache_hit_rate                           # Gauge (target: >80%)
kafka_consumer_lag                             # Gauge
```

### Grafana Dashboards

1. **Agent Performance Dashboard**
   - Tickets processed (last 24h)
   - Average response time by channel
   - Escalation rate trend
   - Sentiment distribution

2. **Infrastructure Health Dashboard**
   - Database connection pool status
   - Redis cache hit rate
   - Kafka consumer lag
   - Pod CPU/memory usage

3. **Business Metrics Dashboard**
   - CSAT score trend
   - First-contact resolution rate
   - Top 10 categories by volume
   - Multilingual breakdown

### Alerts (PagerDuty)

```yaml
# Critical (Page immediately)
- name: GeminiAPIDown
  condition: gemini_api_errors_total > 10 in 5m
  severity: critical

- name: DatabaseDown
  condition: db_connection_errors_total > 5 in 1m
  severity: critical

- name: HighEscalationRate
  condition: escalation_rate > 0.50 for 15m
  severity: critical

# Warning (Slack notification)
- name: SlowResponseTime
  condition: response_time_seconds{p90} > 5s for 10m
  severity: warning

- name: LowCacheHitRate
  condition: redis_cache_hit_rate < 0.60 for 15m
  severity: warning

- name: HighKafkaLag
  condition: kafka_consumer_lag > 1000 for 5m
  severity: warning
```

---

## Deployment Workflow (CI/CD)

```
Developer pushes to main branch
         │
         ▼
GitHub Actions workflow triggered
         │
         ├──► Run pytest (131 tests must pass)
         ├──► Run mypy (type checking)
         ├──► Run ruff (linting)
         └──► Run security scan (bandit)
         │
         ▼
Build Docker image
         │
         ├──► Tag: gcr.io/project/crm-digital:git-sha
         └──► Push to Google Container Registry
         │
         ▼
Deploy to staging environment
         │
         ├──► kubectl apply -f k8s/staging/
         ├──► Run smoke tests
         └──► Run integration tests
         │
         ▼
Manual approval gate (Slack button)
         │
         ▼
Deploy to production (canary)
         │
         ├──► Deploy to 10% of pods
         ├──► Monitor error rate for 15 minutes
         └──► If error_rate < 1%, continue
         │
         ▼
Full production rollout
         │
         ├──► kubectl apply -f k8s/production/
         └──► Monitor metrics for 1 hour
         │
         ▼
Mark deployment as successful
```

---

## Database Schema (PostgreSQL)

```sql
-- Customers (primary identity)
CREATE TABLE customers (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    name          TEXT,
    phone         TEXT,
    company       TEXT,
    plan          TEXT DEFAULT 'free',
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_plan ON customers(plan);

-- Tickets (conversation container)
CREATE TABLE tickets (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id       UUID REFERENCES customers(id) ON DELETE SET NULL,
    channel           TEXT NOT NULL,
    status            TEXT DEFAULT 'open',
    priority          TEXT DEFAULT 'medium',
    subject           TEXT NOT NULL,
    sentiment_score   FLOAT,
    escalated_to      TEXT,
    resolved_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_created ON tickets(created_at DESC);
CREATE INDEX idx_tickets_active ON tickets(customer_id, status) 
    WHERE status IN ('open', 'in_progress');

-- Messages (conversation turns)
CREATE TABLE messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id   UUID REFERENCES tickets(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,  -- 'customer' | 'agent' | 'system'
    body        TEXT NOT NULL,
    raw_payload JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_ticket ON messages(ticket_id, created_at);

-- Knowledge Base
CREATE TABLE knowledge_base (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category    TEXT NOT NULL,
    problem     TEXT NOT NULL,
    solution    TEXT NOT NULL,
    plan_gates  TEXT[],  -- ['starter', 'pro', 'enterprise']
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_kb_category ON knowledge_base(category);
CREATE INDEX idx_kb_search ON knowledge_base USING gin(to_tsvector('english', problem || ' ' || solution));

-- Daily Reports (analytics)
CREATE TABLE daily_reports (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_date            DATE UNIQUE NOT NULL,
    total_tickets          INT,
    escalation_rate        FLOAT,
    avg_sentiment          FLOAT,
    top_categories         JSONB,
    channel_breakdown      JSONB,
    generated_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_date ON daily_reports(report_date DESC);
```

---

## Configuration Files

### Docker Compose (Local Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: crm_digital
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  app:
    build: .
    command: uvicorn src.api.main:app --host 0.0.0.0 --reload
    environment:
      DATABASE_URL: postgresql+asyncpg://dev:dev@postgres/crm_digital
      REDIS_URL: redis://redis:6379
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      - postgres
      - redis
      - kafka

volumes:
  postgres_data:
```

### GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov
      - run: mypy src/
      - run: ruff check src/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: gcr.io
          username: _json_key
          password: ${{ secrets.GCR_JSON_KEY }}
      - run: |
          docker build -t gcr.io/${{ secrets.GCP_PROJECT }}/crm-digital:${{ github.sha }} .
          docker push gcr.io/${{ secrets.GCP_PROJECT }}/crm-digital:${{ github.sha }}

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/setup-gcloud@v1
      - run: |
          gcloud container clusters get-credentials staging --region us-central1
          kubectl set image deployment/fastapi-webhooks \
            fastapi=gcr.io/${{ secrets.GCP_PROJECT }}/crm-digital:${{ github.sha }}
          kubectl rollout status deployment/fastapi-webhooks

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: google-github-actions/setup-gcloud@v1
      - run: |
          gcloud container clusters get-credentials production --region us-central1
          kubectl set image deployment/fastapi-webhooks \
            fastapi=gcr.io/${{ secrets.GCP_PROJECT }}/crm-digital:${{ github.sha }}
          kubectl rollout status deployment/fastapi-webhooks --timeout=10m
```

---

**Document Status:** ✅ Complete  
**Architecture Review:** _[Pending]_  
**Infrastructure Provisioning:** _[Pending]_
