-- CRM Digital — PostgreSQL Schema
-- This database IS the CRM. No external CRM required.

-- ─────────────────────────────────────────────
-- 1. Customers
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE NOT NULL,
    name            TEXT,
    phone           TEXT,          -- WhatsApp number e.g. +1234567890
    company         TEXT,
    plan            TEXT,          -- free | starter | pro | enterprise
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────
-- 2. Tickets
-- ─────────────────────────────────────────────
CREATE TYPE ticket_status AS ENUM (
    'open', 'in_progress', 'waiting_customer', 'escalated', 'resolved', 'closed'
);

CREATE TYPE ticket_priority AS ENUM ('low', 'medium', 'high', 'critical');

CREATE TYPE ticket_channel AS ENUM ('email', 'whatsapp', 'web_form');

CREATE TABLE IF NOT EXISTS tickets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     UUID REFERENCES customers(id) ON DELETE SET NULL,
    channel         ticket_channel NOT NULL,
    status          ticket_status DEFAULT 'open',
    priority        ticket_priority DEFAULT 'medium',
    subject         TEXT NOT NULL,
    sentiment_score FLOAT,         -- -1.0 (negative) to 1.0 (positive)
    escalated_to    TEXT,          -- human agent name / queue
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────
-- 3. Messages (conversation turns on a ticket)
-- ─────────────────────────────────────────────
CREATE TYPE message_role AS ENUM ('customer', 'agent', 'system');

CREATE TABLE IF NOT EXISTS messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id       UUID REFERENCES tickets(id) ON DELETE CASCADE,
    role            message_role NOT NULL,
    body            TEXT NOT NULL,
    raw_payload     JSONB,         -- original webhook payload
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────
-- 4. Knowledge Base (agent learns from resolved tickets)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_base (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_ticket   UUID REFERENCES tickets(id) ON DELETE SET NULL,
    category        TEXT,
    problem         TEXT NOT NULL,
    solution        TEXT NOT NULL,
    usefulness      INT DEFAULT 0,  -- upvoted by agent when reused
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────
-- 5. Daily Sentiment Reports
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_date     DATE UNIQUE NOT NULL,
    total_tickets   INT,
    resolved        INT,
    escalated       INT,
    avg_sentiment   FLOAT,
    top_issues      JSONB,          -- [{"category": "billing", "count": 12}, ...]
    summary_text    TEXT,           -- Claude-generated narrative
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────
-- Indexes
-- ─────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_tickets_customer  ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status    ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_channel   ON tickets(channel);
CREATE INDEX IF NOT EXISTS idx_messages_ticket   ON messages(ticket_id);
CREATE INDEX IF NOT EXISTS idx_kb_category       ON knowledge_base(category);

-- ─────────────────────────────────────────────
-- Auto-update updated_at
-- ─────────────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_customers_updated BEFORE UPDATE ON customers
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_tickets_updated BEFORE UPDATE ON tickets
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
