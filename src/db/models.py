"""
SQLAlchemy async models — mirrors schema.sql.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON, Column, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class TicketStatus(str, PyEnum):
    open = "open"
    in_progress = "in_progress"
    waiting_customer = "waiting_customer"
    escalated = "escalated"
    resolved = "resolved"
    closed = "closed"

class TicketPriority(str, PyEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class TicketChannel(str, PyEnum):
    email = "email"
    whatsapp = "whatsapp"
    web_form = "web_form"

class MessageRole(str, PyEnum):
    customer = "customer"
    agent = "agent"
    system = "system"


# ── Tables ────────────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email      = Column(String, unique=True, nullable=False)
    name       = Column(String)
    phone      = Column(String)
    company    = Column(String)
    plan       = Column(String, default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tickets    = relationship("Ticket", back_populates="customer")


class Ticket(Base):
    __tablename__ = "tickets"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id     = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"))
    channel         = Column(String, nullable=False)
    status          = Column(String, default=TicketStatus.open)
    priority        = Column(String, default=TicketPriority.medium)
    subject         = Column(Text, nullable=False)
    sentiment_score = Column(Float)
    escalated_to    = Column(String)
    resolved_at     = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer  = relationship("Customer", back_populates="tickets")
    messages  = relationship("Message", back_populates="ticket", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id   = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"))
    role        = Column(String, nullable=False)
    body        = Column(Text, nullable=False)
    raw_payload = Column(JSON)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket", back_populates="messages")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_ticket = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="SET NULL"))
    category      = Column(String)
    problem       = Column(Text, nullable=False)
    solution      = Column(Text, nullable=False)
    usefulness    = Column(Integer, default=0)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_date  = Column(Date, unique=True, nullable=False)
    total_tickets = Column(Integer)
    resolved     = Column(Integer)
    escalated    = Column(Integer)
    avg_sentiment = Column(Float)
    top_issues   = Column(JSON)
    summary_text = Column(Text)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
