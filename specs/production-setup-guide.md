# Production Setup Guide

**Complete file templates and setup instructions for production code structure.**

---

## Quick Setup

### Step 1: Create Directory Structure

Run ONE of these options:

**Option A: Batch Script (Windows)**
```cmd
cd C:\Users\Amena\Desktop\crm-digital
setup_production.bat
```

**Option B: Python Script**
```cmd
cd C:\Users\Amena\Desktop\crm-digital  
python setup_production.py
```

**Option C: Manual**
```cmd
cd C:\Users\Amena\Desktop\crm-digital
mkdir production
cd production
mkdir agent channels workers api database\migrations tests k8s
```

### Step 2: Create Initial Files

After directories exist, create these files:

#### production/__init__.py
```python
"""Production CRM Digital Agent"""
__version__ = "1.0.0"
```

#### production/agent/__init__.py
```python
"""Production Agent Module"""
from .customer_success_agent import run_agent
from .tools import FUNCTION_TOOLS

__all__ = ["run_agent", "FUNCTION_TOOLS"]
```

#### production/channels/__init__.py
```python
"""Channel Handlers"""
```

#### production/workers/__init__.py  
"""Background Workers"""
```

#### production/api/__init__.py
```python
"""FastAPI Application"""
```

#### production/database/__init__.py
```python
"""Database Layer"""
```

#### production/tests/__init__.py
```python
"""Production Tests"""
```

---

## Directory Structure

```
production/
├── agent/                     # Gemini-powered agent
│   ├── __init__.py
│   ├── customer_success_agent.py
│   ├── tools.py
│   ├── prompts.py
│   └── formatters.py
├── channels/                  # Channel integrations  
│   ├── __init__.py
│   ├── gmail_handler.py
│   ├── whatsapp_handler.py
│   └── web_form_handler.py
├── workers/                   # Background workers
│   ├── __init__.py
│   ├── message_processor.py
│   └── metrics_collector.py
├── api/                       # FastAPI app
│   ├── __init__.py
│   └── main.py
├── database/                  # Database layer
│   ├── __init__.py
│   ├── schema.sql
│   ├── migrations/
│   └── queries.py
├── tests/                     # Production tests
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_channels.py
│   └── test_e2e.py
├── k8s/                       # Kubernetes manifests
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Complete File Templates

For complete file contents, see:
- `specs/code-mapping.md` - Detailed migration guide
- Agent files saved earlier (customer_success_agent.py, tools.py, prompts.py, formatters.py)

---

## Migration Workflow

1. **Create structure** (this guide)
2. **Copy prototype logic** (from src/ to production/)
3. **Migrate to Gemini** (replace rules with function calling)
4. **Add observability** (structlog, Kafka, OpenTelemetry)
5. **Deploy to K8s** (use k8s/ manifests)

---

## Task Tracking

Use SQL database to track progress:

```sql
-- View ready tasks (no pending dependencies)
SELECT id, task_name, estimated_hours, phase
FROM migration_tasks
WHERE status = 'pending'
AND NOT EXISTS (
    SELECT 1 FROM task_deps td
    JOIN migration_tasks dep ON td.depends_on = dep.id
    WHERE td.task_id = migration_tasks.id AND dep.status != 'done'
)
ORDER BY phase, priority;
```

Mark tasks as done:
```sql
UPDATE migration_tasks SET status = 'done' WHERE id = 'db-migrations';
```

---

## Next Steps

1. ✅ Run setup script to create directories
2. ✅ Create __init__.py files in each directory
3. ✅ Review `specs/code-mapping.md` for file contents
4. ✅ Start Phase 1: Database & Core Agent (8 tasks, 53h)
5. ✅ Track progress in SQL database

---

**Created:** 2026-04-03  
**Purpose:** Production code setup instructions  
**Status:** Ready for execution
