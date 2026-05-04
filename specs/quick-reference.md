# Quick Reference: Prototype → Production

## 🗂️ File Mapping (At a Glance)

```
PROTOTYPE                          →  PRODUCTION
────────────────────────────────────────────────────────────────
src/core_loop_prototype.py        →  src/agent/core_loop.py
src/conversation_state.py          →  DB queries + Redis cache
src/mcp_server.py                  →  src/agent/tools.py (@function_tool)
tests/ (131 tests)                 →  tests/ (keep + add 50+ more)

NEW IN PRODUCTION:
  src/agent/agent.py               ← Main entry point (Gemini loop)
  src/agent/resilience.py          ← Retry + circuit breakers
  src/events/producer.py           ← Kafka event streaming
  src/observability/               ← Logging, metrics, tracing
  k8s/                             ← Kubernetes manifests
  .github/workflows/deploy.yml     ← CI/CD pipeline
```

---

## 🔄 Code Transformation Examples

### Example 1: Language Detection

**Before (Prototype):**
```python
def detect_language(text: str) -> str:
    for lang, pattern in _LANGUAGE_HINTS.items():
        if pattern.search(text):
            return lang
    return "English"
```

**After (Production):**
```python
async def detect_language(text: str, gemini_client) -> str:
    """Detect language using Gemini 1.5 Pro."""
    prompt = f"Detect the language of this text. Reply with just the language name: {text[:200]}"
    response = await gemini_client.generate_content(prompt)
    return response.text.strip() or "English"
```

---

### Example 2: Conversation State

**Before (Prototype):**
```python
# In-memory dict
memory = ConversationMemory()
session = memory.get_active_session(email)
```

**After (Production):**
```python
# Database query
async def get_active_session(db: AsyncSession, customer_id: str) -> Ticket | None:
    result = await db.execute(
        select(Ticket)
        .where(Ticket.customer_id == customer_id)
        .where(Ticket.status.in_(["open", "in_progress"]))
        .order_by(Ticket.updated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
```

---

### Example 3: Logging

**Before (Prototype):**
```python
print(f"[stitch] Creating NotebookLM notebook for '{customer_name}'...")
```

**After (Production):**
```python
import structlog
logger = structlog.get_logger()

logger.info(
    "notebook.create.start",
    customer_name=customer_name,
    notebook_id=notebook_id,
    sources_count=len(files),
)
```

---

### Example 4: Error Handling

**Before (Prototype):**
```python
result = subprocess.run(["notebooklm", "create", name], capture_output=True)
if result.returncode != 0:
    raise RuntimeError(f"Failed: {result.stderr}")
```

**After (Production):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def create_notebook(name: str) -> str:
    try:
        result = await subprocess_run(["notebooklm", "create", name])
        return result.notebook_id
    except Exception as e:
        logger.error("notebook.create.failed", error=str(e), name=name)
        raise
```

---

## 📊 Key Metrics Dashboard

### What to Monitor in Production

```
┌────────────────────────────────────────────────────────────┐
│ AGENT PERFORMANCE                                          │
├────────────────────────────────────────────────────────────┤
│ Tickets processed (24h)          │ 1,247         ↑ 12%   │
│ Average response time            │ 2.3s          ✓ OK    │
│ Escalation rate                  │ 18%           ✓ OK    │
│ CSAT score                       │ 4.2/5.0       ✓ OK    │
│ First-contact resolution         │ 73%           ✓ OK    │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE                                             │
├────────────────────────────────────────────────────────────┤
│ Active pods                      │ 5/10          ✓ OK    │
│ Database connections (active)    │ 12/20         ✓ OK    │
│ Redis cache hit rate             │ 87%           ✓ OK    │
│ Kafka consumer lag               │ 23 messages   ✓ OK    │
│ CPU utilization                  │ 45%           ✓ OK    │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ ALERTS (Last 24h)                                          │
├────────────────────────────────────────────────────────────┤
│ 🟢 No critical alerts                                      │
│ 🟡 1 warning: Slow response time spike (resolved)         │
│ 🟢 0 escalation false negatives detected                   │
└────────────────────────────────────────────────────────────┘
```

---

## 🚨 Troubleshooting Guide

### Common Issues & Quick Fixes

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| **Response time >5s** | Gemini API slow | Check circuit breaker status, fallback to rules |
| **Escalation false negative** | Keyword miss | Manual escalate, add keyword to DB |
| **Database timeout** | Connection pool exhausted | Increase pool size, check slow queries |
| **Channel delivery failure** | Gmail/Twilio API down | Check dead-letter queue, retry manually |
| **Tests failing** | DB schema mismatch | Run `alembic upgrade head` |
| **High CPU usage** | Too many concurrent Gemini calls | Reduce HPA max replicas, add rate limiting |

---

## 📋 Pre-Deployment Checklist

Before deploying to production:

```
Phase 1: Database & Core Agent
  [x] Alembic migrations run successfully
  [x] Knowledge base seeded (12 entries)
  [x] Gemini API key configured
  [x] Core loop migrated to Gemini
  [x] All 131 tests passing
  [x] Database indexes created
  [x] Connection pooling configured (max 20)

Phase 2: Channel Handlers
  [x] Gmail OAuth working
  [x] Gmail threading tested (multi-turn conversation)
  [x] WhatsApp webhook signature validation
  [x] Web form CORS + rate limiting
  [x] Retry logic tested (3 attempts)
  [x] Circuit breakers configured

Phase 3: Observability
  [x] All print() replaced with structlog
  [x] Kafka topics created (escalations, tickets)
  [x] OpenTelemetry tracing active
  [x] Prometheus metrics exposed
  [x] Grafana dashboards deployed
  [x] Sentry error tracking configured

Phase 4: Infrastructure
  [x] Kubernetes manifests validated
  [x] CI/CD pipeline tested on staging
  [x] Staging environment healthy (1 week)
  [x] Load testing completed (1000 req/s)
  [x] HPA tuned (scale at 70% CPU)

Phase 5: Production Readiness
  [x] Security audit passed
  [x] Secrets rotation policy documented
  [x] On-call runbook reviewed
  [x] Rollback plan tested
  [x] User acceptance testing (2 weeks)
  [x] CSAT >4.0 for 1 week
```

---

## 🎯 Daily Standup Template

```
What did we complete yesterday?
  - Task ID: db-migrations (Phase 1)
  - Task ID: db-seed-kb (Phase 1)

What are we working on today?
  - Task ID: core-loop-gemini (Phase 1) — 50% complete
  - Task ID: conv-memory-db (Phase 1) — starting

Any blockers?
  - Waiting for Gemini API key approval (Ops team)
  - Need staging database credentials

Risk alerts:
  - 🟡 core-loop-gemini taking longer than estimated (16h → 20h)
  - 🟢 All tests still passing
```

---

## 📦 Environment Variables Reference

```bash
# ── AI / LLM ───────────────────────────────────────────────
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-pro
ANTHROPIC_API_KEY=your_key_here

# ── Database ───────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# ── Redis Cache ────────────────────────────────────────────
REDIS_URL=redis://host:6379
REDIS_SESSION_TTL_SECONDS=3600

# ── Kafka Events ───────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_ESCALATIONS=escalations
KAFKA_TOPIC_TICKETS=tickets

# ── Channels ───────────────────────────────────────────────
GMAIL_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# ── Agent Configuration ────────────────────────────────────
SESSION_TIMEOUT_MINUTES=60
KB_MATCH_THRESHOLD=0.8
MAX_RETRIES=3
ESCALATION_SLA_SECURITY_HOURS=2
ESCALATION_SLA_LEGAL_HOURS=24

# ── Observability ──────────────────────────────────────────
LOG_LEVEL=INFO
SENTRY_DSN=https://...
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
PROMETHEUS_PORT=9090
```

---

## 🔗 Related Documents

| Document | Purpose | When to Read |
|----------|---------|--------------|
| `specs/transition-checklist.md` | Full transition guide with prompts, edge cases | Before starting migration |
| `specs/code-mapping.md` | Detailed file-by-file mapping | During implementation |
| `specs/production-architecture.md` | Architecture diagrams, data flows | Infrastructure setup |
| `specs/migration-summary.md` | 30-task breakdown, 199 hours | Project planning |
| `specs/discovery-log.md` | Original 55-ticket analysis | Understanding requirements |
| `specs/customer-success-fte-spec.md` | Agent specification | Reference implementation |

---

## 🚀 Getting Started (First Day)

### For Backend Engineers

```bash
# 1. Set up local environment
git clone https://github.com/your-org/crm-digital.git
cd crm-digital
cp .env.example .env
# Edit .env with your API keys

# 2. Start dependencies
docker-compose up -d postgres redis kafka

# 3. Run database migrations
alembic upgrade head

# 4. Seed knowledge base
python scripts/seed_kb.py

# 5. Run tests
pytest tests/ -v

# 6. Start the prototype (validate setup)
python -m src.core_loop_prototype

# 7. Start FastAPI (production)
uvicorn src.api.main:app --reload
```

### For SRE/DevOps

```bash
# 1. Provision staging cluster
gcloud container clusters create crm-staging \
  --region us-central1 \
  --num-nodes 3 \
  --machine-type n1-standard-2

# 2. Set up Cloud SQL
gcloud sql instances create crm-postgres \
  --database-version POSTGRES_15 \
  --tier db-f1-micro \
  --region us-central1

# 3. Deploy application
kubectl apply -f k8s/staging/

# 4. Verify deployment
kubectl get pods
kubectl logs deployment/fastapi-webhooks
curl http://<EXTERNAL_IP>/health

# 5. Run smoke tests
pytest tests/integration/ -v
```

---

## 📞 Support Contacts

| Team | Contact | Responsibility |
|------|---------|----------------|
| Engineering | @eng-team | Code changes, bug fixes |
| SRE/DevOps | @sre-team | Infrastructure, deployments |
| Product | @product-team | Requirements, prioritization |
| Support | @support-team | User acceptance testing |
| Security | @security-team | Security audit, compliance |

---

**Last Updated:** 2026-04-03  
**Next Update:** After Phase 1 completion  
**Questions?** Post in #crm-digital-migration Slack channel
