# Code Mapping: Prototype → Production

**Project:** CRM Digital — Customer Success Agent  
**Date:** 2026-04-03  
**Purpose:** Map incubation code to production architecture

---

## 📊 High-Level Mapping Table

| INCUBATION (What you built) | PRODUCTION (Where it goes) | Status |
|-----------------------------|----------------------------|--------|
| Prototype Python script | `agent/customer_success_agent.py` | ✅ Exists |
| MCP server tools | `@function_tool` decorated functions | ✅ Exists |
| In-memory conversation | PostgreSQL `messages` table | ✅ Exists |
| Print statements | Structured logging + Kafka events | ⚠️ Partial |
| Manual testing | pytest test suite | ✅ Exists (131 tests) |
| Local file storage | PostgreSQL + S3/MinIO | ⚠️ Partial (PG only) |
| Single-threaded | Async workers on Kubernetes | 🔄 In progress |
| Hardcoded config | Environment variables + ConfigMaps | ⚠️ Partial |
| Direct API calls | Channel handlers with retry logic | ✅ Exists |

---

## 🗂️ Detailed File Mapping

### 1. Core Agent Logic

#### `src/core_loop_prototype.py` → Multiple Production Files

| Prototype Function | Production Location | Notes |
|-------------------|---------------------|-------|
| `process_ticket()` | `src/agent/agent.py:run_agent()` | Main entry point |
| `detect_language()` | `src/agent/core_loop.py:detect_language()` | Gemini-powered version |
| `check_escalation()` | `src/agent/core_loop.py:check_escalation()` | Enhanced with DB logging |
| `classify_category()` | `src/agent/core_loop.py:classify_category()` | Gemini-powered version |
| `estimate_sentiment()` | `src/agent/core_loop.py:estimate_sentiment()` | Gemini-powered version |
| `_find_kb()` | `src/agent/tools.py:search_knowledge_base()` | DB-backed, async |
| `_build_reply()` | `src/agent/core_loop.py:build_reply()` | Gemini-powered with templates |
| `_format_escalation()` | `src/agent/core_loop.py:format_escalation()` | Template-based |
| `_sign_off()` | `src/agent/core_loop.py:apply_channel_formatting()` | Enhanced with brand voice |

**Migration Steps:**
1. ✅ Keep `core_loop_prototype.py` for test suite compatibility
2. 🔄 Implement Gemini versions in `core_loop.py`
3. 🔄 Add async/await throughout
4. 🔄 Replace regex patterns with DB queries for escalation triggers
5. 🔄 Add structured logging for each step

---

### 2. Conversation Memory & State

#### `src/conversation_state.py` → Database Tables

| Prototype Class | Production Table/Model | Notes |
|----------------|----------------------|-------|
| `CustomerProfile` | `src/db/models.py:Customer` | PostgreSQL table |
| `ConversationSession` | `src/db/models.py:Ticket` | Maps to ticket lifecycle |
| `ConversationTurn` | `src/db/models.py:Message` | Each message is a turn |
| `ConversationMemory` (in-memory dict) | PostgreSQL session queries | Query-based retrieval |

**Migration Steps:**
1. ✅ Database models already exist
2. 🔄 Migrate `ConversationMemory.get_active_session()` to SQL query:
   ```python
   # Before (in-memory)
   session = memory.get_active_session(email)
   
   # After (DB query)
   ticket = await db.execute(
       select(Ticket)
       .where(Ticket.customer_id == customer.id)
       .where(Ticket.status.in_(["open", "in_progress"]))
       .order_by(Ticket.updated_at.desc())
   )
   ```
3. 🔄 Replace session timeout logic with DB triggers or background jobs
4. 🔄 Add indexes: `(customer_id, status, updated_at)` for fast lookups

---

### 3. MCP Server Tools

#### `src/mcp_server.py` → Gemini Function Tools

| MCP Tool | Production Function | Location | Status |
|----------|-------------------|----------|--------|
| `search_knowledge_base()` | `search_knowledge_base()` | `src/agent/tools.py` | ✅ Exists |
| `create_ticket()` | `create_ticket()` | `src/agent/tools.py` | ✅ Exists |
| `get_customer_history()` | `get_customer_history()` | `src/agent/tools.py` | ✅ Exists |
| `escalate_to_human()` | `escalate_to_human()` | `src/agent/tools.py` | ✅ Exists |
| `send_response()` | `send_response()` | `src/agent/tools.py` | ✅ Exists |
| `get_ticket_status()` | `get_ticket_status()` | `src/agent/tools.py` | ✅ Exists |
| `get_dashboard()` | `get_dashboard()` | `src/agent/tools.py` | ✅ Exists |
| `process_customer_message()` | `run_agent()` | `src/agent/agent.py` | ✅ Exists |

**Migration Steps:**
1. ✅ MCP tools already implemented in `tools.py`
2. 🔄 Add Gemini function schemas in `tool_schemas.py`
3. 🔄 Wrap each tool with `@function_tool` decorator:
   ```python
   from google.generativeai import function_tool
   
   @function_tool
   async def search_knowledge_base(db: AsyncSession, query: str, plan: str) -> dict:
       """Search product docs for relevant info."""
       # implementation
   ```
4. 🔄 Add retry logic with exponential backoff for DB calls
5. 🔄 Add circuit breakers for external APIs (Twilio, Gmail)

---

### 4. Channel Handlers

#### Prototype Direct Calls → Production Channel Adapters

| Channel | Prototype | Production File | Features |
|---------|-----------|----------------|----------|
| Email | Print to console | `src/channels/gmail.py` | Gmail API, threading, OAuth |
| WhatsApp | Print to console | `src/channels/whatsapp.py` | Twilio API, media handling |
| Web Form | Print to console | `src/channels/web_form.py` | FastAPI endpoint, validation |

**Migration Steps:**
1. ✅ Channel handlers already stubbed
2. 🔄 Implement `src/channels/gmail.py`:
   - OAuth flow for service account
   - Thread tracking (In-Reply-To header)
   - Attachment download to S3
   - Retry logic for send failures
3. 🔄 Implement `src/channels/whatsapp.py`:
   - Twilio webhook signature validation
   - Media message support (images, PDFs)
   - Status callbacks (delivered, read)
4. 🔄 Implement `src/channels/web_form.py`:
   - CORS validation
   - Rate limiting per IP
   - CAPTCHA integration

---

### 5. Database Layer

#### In-Memory Dicts → PostgreSQL Tables

| Prototype Data Structure | Production Table | Schema File |
|-------------------------|-----------------|-------------|
| `_tickets: dict[str, dict]` | `tickets` table | `src/db/schema.sql` |
| `memory._profiles: dict` | `customers` table | `src/db/schema.sql` |
| `memory._sessions: dict` | `tickets` + `messages` | `src/db/schema.sql` |
| `_KB_SEED: dict` | `knowledge_base` table | `src/db/schema.sql` |

**Migration Steps:**
1. ✅ Tables already defined in `schema.sql` and `models.py`
2. 🔄 Create Alembic migrations:
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```
3. 🔄 Seed knowledge base from prototype dict:
   ```python
   # Migration script
   from src.core_loop_prototype import _KB_SEED
   
   async def seed_kb(db: AsyncSession):
       for keyword, solution in _KB_SEED.items():
           kb = KnowledgeBase(
               category=infer_category(keyword),
               problem=keyword,
               solution=solution,
           )
           db.add(kb)
       await db.commit()
   ```
4. 🔄 Add connection pooling (asyncpg, max 20 connections)
5. 🔄 Add read replicas for `search_knowledge_base()` queries

---

### 6. Configuration Management

#### Hardcoded Values → Environment Variables

| Prototype Constant | Production Env Var | Default | Validation |
|-------------------|-------------------|---------|------------|
| `SESSION_TIMEOUT = timedelta(hours=1)` | `SESSION_TIMEOUT_MINUTES` | `60` | Integer, 1-1440 |
| `_PLAN_LIMITS` dict | `PLAN_CONFIG_JSON` | JSON file | JSON schema |
| Model: "gemini-1.5-pro" | `GEMINI_MODEL` | `gemini-1.5-pro` | Enum |
| KB match threshold | `KB_MATCH_THRESHOLD` | `0.8` | Float, 0.0-1.0 |
| Escalation queues | `ESCALATION_QUEUES_JSON` | JSON file | JSON schema |

**Migration Steps:**
1. 🔄 Create `.env.example`:
   ```bash
   # AI
   GEMINI_API_KEY=your_key_here
   GEMINI_MODEL=gemini-1.5-pro
   ANTHROPIC_API_KEY=your_key_here
   
   # Database
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost/crm_digital
   DB_POOL_SIZE=20
   
   # Channels
   GMAIL_SERVICE_ACCOUNT_JSON=path/to/service-account.json
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   
   # Agent Config
   SESSION_TIMEOUT_MINUTES=60
   KB_MATCH_THRESHOLD=0.8
   MAX_RETRIES=3
   
   # Observability
   LOG_LEVEL=INFO
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   SENTRY_DSN=https://...
   ```
2. 🔄 Add validation with Pydantic:
   ```python
   from pydantic_settings import BaseSettings
   
   class Settings(BaseSettings):
       gemini_api_key: str
       database_url: str
       session_timeout_minutes: int = 60
       
       class Config:
           env_file = ".env"
   ```
3. 🔄 Kubernetes ConfigMap for non-secrets:
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: agent-config
   data:
     SESSION_TIMEOUT_MINUTES: "60"
     KB_MATCH_THRESHOLD: "0.8"
   ```

---

### 7. Testing Infrastructure

#### Manual Testing → Automated Test Suite

| Prototype Testing | Production Testing | Location |
|------------------|-------------------|----------|
| Manual `python -m src.core_loop_prototype` | `pytest tests/test_core_loop.py` | ✅ 45 tests |
| Print debugging | `pytest tests/test_conversation_state.py` | ✅ 26 tests |
| Ad-hoc MCP calls | `pytest tests/test_mcp_server.py` | ✅ 24 tests |
| Manual KB checks | `pytest tests/test_skills.py` | ✅ 36 tests |

**Additional Tests Needed:**
1. 🔄 **Integration tests** (`tests/integration/`):
   - `test_email_to_reply_flow.py` — End-to-end Gmail webhook → DB → reply
   - `test_whatsapp_to_escalation_flow.py` — WhatsApp → escalation → Slack notification
   - `test_web_form_multilingual.py` — French form submission → French reply
2. 🔄 **Load tests** (`tests/load/`):
   - `test_concurrent_tickets.py` — 100 simultaneous tickets
   - `test_kb_search_performance.py` — 1000 searches/second
3. 🔄 **Contract tests** (`tests/contracts/`):
   - `test_twilio_webhook_schema.py` — Validate Twilio payload structure
   - `test_gemini_function_calling.py` — Validate Gemini tool schemas
4. 🔄 **Chaos tests** (`tests/chaos/`):
   - `test_db_connection_failure.py` — Database goes down mid-request
   - `test_gemini_timeout.py` — Gemini API times out

---

### 8. Logging & Observability

#### Print Statements → Structured Logging + Events

| Prototype | Production | Tool | Format |
|-----------|-----------|------|--------|
| `print(f"[stitch] Creating notebook...")` | `logger.info("notebook.create", notebook_id=...)` | `structlog` | JSON |
| `print(f"[stitch] Escalation: {queue}")` | `kafka.send("escalations", event=...)` | Kafka | Avro |
| N/A | Distributed tracing | OpenTelemetry | Spans |
| N/A | Metrics | Prometheus | Gauges/Counters |

**Migration Steps:**
1. 🔄 Replace all `print()` with `structlog`:
   ```python
   import structlog
   
   logger = structlog.get_logger()
   
   # Before
   print(f"[stitch] Creating NotebookLM notebook for '{customer_name}'...")
   
   # After
   logger.info(
       "notebook.create.start",
       customer_name=customer_name,
       notebook_id=notebook_id,
   )
   ```
2. 🔄 Add Kafka event producer for key events:
   ```python
   from aiokafka import AIOKafkaProducer
   
   async def emit_event(topic: str, event: dict):
       await producer.send(topic, value=event)
   
   # Usage
   await emit_event("escalations", {
       "ticket_id": ticket_id,
       "queue": "security-team",
       "reason": "account compromise",
       "timestamp": datetime.utcnow().isoformat(),
   })
   ```
3. 🔄 Add OpenTelemetry spans:
   ```python
   from opentelemetry import trace
   
   tracer = trace.get_tracer(__name__)
   
   with tracer.start_as_current_span("agent.process_ticket") as span:
       span.set_attribute("ticket_id", ticket_id)
       span.set_attribute("channel", channel)
       result = await process_ticket(...)
   ```
4. 🔄 Add Prometheus metrics:
   ```python
   from prometheus_client import Counter, Histogram
   
   tickets_total = Counter("tickets_total", "Total tickets", ["channel", "status"])
   response_time = Histogram("response_time_seconds", "Response time")
   
   tickets_total.labels(channel="email", status="resolved").inc()
   response_time.observe(elapsed_seconds)
   ```

---

### 9. Error Handling & Resilience

#### Direct Calls → Retry Logic + Circuit Breakers

| Prototype Error Handling | Production Pattern | Library |
|-------------------------|-------------------|---------|
| `if result.returncode != 0: raise RuntimeError(...)` | Retry with exponential backoff | `tenacity` |
| No timeout handling | Request timeouts (5s default) | `httpx` |
| No rate limiting | Token bucket rate limiter | `aiolimiter` |
| No circuit breaker | Fail-fast after 5 consecutive errors | `pybreaker` |

**Migration Steps:**
1. 🔄 Add retry logic to all external calls:
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       reraise=True,
   )
   async def call_gemini(prompt: str) -> str:
       response = await gemini_client.generate_content(prompt)
       return response.text
   ```
2. 🔄 Add circuit breakers for critical dependencies:
   ```python
   from pybreaker import CircuitBreaker
   
   gmail_breaker = CircuitBreaker(fail_max=5, timeout_duration=60)
   
   @gmail_breaker
   async def send_email(to: str, body: str):
       # Gmail API call
   ```
3. 🔄 Add request timeouts everywhere:
   ```python
   import httpx
   
   async with httpx.AsyncClient(timeout=5.0) as client:
       response = await client.post(url, json=payload)
   ```
4. 🔄 Add graceful degradation:
   ```python
   try:
       kb_results = await search_knowledge_base(query)
   except Exception as e:
       logger.error("kb.search.failed", error=str(e))
       kb_results = []  # Degrade to empty results, don't fail entire request
   ```

---

### 10. Deployment Architecture

#### Single Process → Distributed Async Workers

| Component | Deployment Target | Replicas | Scaling |
|-----------|------------------|----------|---------|
| MCP Server (dev) | Local stdio | 1 | Manual |
| FastAPI Webhooks | Kubernetes Deployment | 3-10 | HPA (CPU 70%) |
| Async Worker (tickets) | Kubernetes Deployment | 5-20 | HPA (queue depth) |
| Async Worker (enrichment) | Kubernetes CronJob | 1 | Scheduled |
| PostgreSQL | Cloud SQL (GCP) / RDS (AWS) | 1 primary + 2 replicas | Auto-failover |
| Redis (session cache) | Cloud Memorystore / ElastiCache | 1 cluster | Auto-scale |
| Kafka (events) | Confluent Cloud / MSK | 3 brokers | Managed |

**Kubernetes Deployment Example:**

```yaml
# k8s/deployments/fastapi-webhooks.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-webhooks
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-webhooks
  template:
    metadata:
      labels:
        app: fastapi-webhooks
    spec:
      containers:
      - name: fastapi
        image: gcr.io/your-project/crm-digital:latest
        command: ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-credentials
              key: gemini-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-webhooks-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-webhooks
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 🔄 Migration Priority Order

### Phase 1: Database & Core Agent (Week 1-2)
1. ✅ Database models exist
2. 🔄 Migrate `core_loop_prototype.py` logic to `agent/core_loop.py` with Gemini
3. 🔄 Replace in-memory `ConversationMemory` with DB queries
4. 🔄 Add async/await throughout
5. 🔄 Test with existing 131-test suite (ensure compatibility)

### Phase 2: Channel Handlers (Week 3)
6. 🔄 Implement Gmail OAuth and threading
7. 🔄 Implement Twilio WhatsApp webhook
8. 🔄 Implement web form endpoint with validation
9. 🔄 Add retry logic and circuit breakers

### Phase 3: Observability (Week 4)
10. 🔄 Replace print statements with structlog
11. 🔄 Add Kafka event streaming
12. 🔄 Add OpenTelemetry tracing
13. 🔄 Add Prometheus metrics

### Phase 4: Infrastructure (Week 5)
14. 🔄 Create Kubernetes manifests
15. 🔄 Set up CI/CD pipeline (GitHub Actions)
16. 🔄 Deploy to staging environment
17. 🔄 Load testing and tuning

### Phase 5: Production Readiness (Week 6)
18. 🔄 Security audit (secrets rotation, RBAC)
19. 🔄 Monitoring dashboards (Grafana)
20. 🔄 Runbook for on-call engineers
21. 🔄 Gradual rollout (see transition-checklist.md)

---

## 📦 Dependency Changes

### Prototype Dependencies
```
# requirements.txt (prototype)
google-generativeai>=0.8.0
anthropic>=0.40.0
mcp>=1.26.0
notebooklm-py
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
pytest>=8.0.0
```

### Production Dependencies (Additional)
```
# requirements.txt (production additions)
# Resilience
tenacity>=8.0.0           # Retry logic
pybreaker>=1.0.0          # Circuit breakers
aiolimiter>=1.1.0         # Rate limiting

# Observability
structlog>=24.0.0         # Structured logging
python-json-logger>=2.0.0 # JSON log formatter
opentelemetry-api>=1.20.0 # Tracing
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation-fastapi>=0.41b0
prometheus-client>=0.19.0 # Metrics

# Messaging
aiokafka>=0.10.0          # Kafka producer/consumer
confluent-kafka>=2.3.0    # Schema registry

# Caching
redis[hiredis]>=5.0.0     # Session caching
aioredis>=2.0.0           # Async Redis

# Configuration
pydantic-settings>=2.0.0  # Env var validation

# Security
python-jose[cryptography]>=3.3.0  # JWT tokens
passlib[bcrypt]>=1.7.0    # Password hashing

# Deployment
alembic>=1.13.0           # Database migrations
gunicorn>=21.0.0          # Production WSGI server
sentry-sdk[fastapi]>=1.40.0  # Error tracking
```

---

## 🧪 Testing Strategy After Migration

### Unit Tests (Keep Existing + Add New)
- ✅ Keep all 131 existing tests (compatibility layer)
- 🔄 Add async versions of each test
- 🔄 Add database fixture tests (rollback after each)
- 🔄 Add mock tests for Gemini API calls

### Integration Tests (New)
- 🔄 FastAPI endpoint → DB → channel reply (all 3 channels)
- 🔄 Escalation flow → Slack notification
- 🔄 Multilingual detection → correct language reply
- 🔄 NotebookLM enrichment → Claude CRM note

### Load Tests (New)
- 🔄 1000 concurrent webhook requests
- 🔄 Database connection pool exhaustion
- 🔄 Gemini API rate limit handling

### Contract Tests (New)
- 🔄 Twilio webhook payload validation
- 🔄 Gmail Pub/Sub payload validation
- 🔄 Gemini function calling schema validation

---

## 🚨 Critical Migration Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Breaking existing tests** | High | Keep `core_loop_prototype.py` as compatibility layer |
| **Database migration data loss** | Critical | Test on staging copy first, backup before prod migration |
| **Gemini API cost explosion** | Medium | Add budget alerts, implement caching, monitor token usage |
| **Session timeout logic change** | Medium | A/B test 1 hour vs DB-based timeout |
| **Channel delivery failures** | High | Add dead-letter queue for failed messages, retry 3x |
| **Performance regression** | Medium | Load test before deployment, keep rollback plan |
| **Escalation false negatives** | Critical | Manual review of first 500 escalations, keep keyword fallback |

---

## ✅ Success Criteria

Migration is complete when:

1. ✅ All 131 existing tests still pass
2. ✅ 50+ new async/integration tests added and passing
3. ✅ Prototype code archived to `archive/` directory (not deleted)
4. ✅ Production code runs on Kubernetes with 99.5% uptime for 1 week
5. ✅ Average response time <3 seconds (90th percentile)
6. ✅ Zero critical escalation false negatives (security/legal/billing)
7. ✅ All print statements replaced with structured logs
8. ✅ Monitoring dashboards operational (Grafana + Prometheus)
9. ✅ On-call runbook reviewed by SRE team
10. ✅ Gradual rollout plan approved by product team

---

**Next Steps:**
1. Review this mapping with engineering team
2. Create GitHub Project board with tasks from Phase 1-5
3. Set up staging environment (Kubernetes + Cloud SQL)
4. Start Phase 1: Database & Core Agent migration
5. Daily standups to track migration progress

---

**Document Status:** ✅ Complete  
**Reviewed By:** _[Pending]_  
**Approved For Migration:** _[Pending]_
