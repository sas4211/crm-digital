"""
Exercise 1.3 — Conversation Memory and State tests.

Tests for:
- ConversationSession: tracking turns, sentiment trend, channel switches, resolution
- ConversationMemory: profile management, session lifecycle, turn recording
- Integration: process_ticket uses conversation memory for follow-up context
"""

from datetime import timedelta

import pytest

from src.conversation_state import (
    ConversationMemory,
    ConversationSession,
    ConversationTurn,
    CustomerProfile,
    SESSION_TIMEOUT,
)


# =====================================================================
# ConversationSession
# =====================================================================

class TestConversationSession:
    """Tests for the ConversationSession data model."""

    def test_session_starts_empty(self):
        session = ConversationSession(
            session_id="S-001",
            customer_email="alice@example.com",
            customer_name="Alice",
            original_channel="email",
            current_channel="email",
        )
        assert session.channel_history == []
        assert session.sentiment_track == []
        assert session.turns == []
        assert session.resolved is False
        assert session.escalated is False
        assert session.avg_sentiment == 0.0
        assert session.sentiment_trend == 0.0

    def test_channel_switch_detected(self):
        session = ConversationSession(
            session_id="S-001b",
            customer_email="alice@example.com",
            customer_name="Alice",
            original_channel="email",
            current_channel="email",
        )
        # First turn: email
        session.add_turn(ConversationTurn(
            timestamp="2026-04-03T10:00:00Z",
            channel="email",
            message_sent="Hi, I need help with automations",
            reply_sent="Hi Alice, I can help with that.",
            topic_detected="automations",
            sentiment_score=0.0,
            escalated=False,
            resolved=False,
        ))
        assert not session.channel_switched
        assert session.channel_history == ["email"]

        # Second turn: WhatsApp
        session.add_turn(ConversationTurn(
            timestamp="2026-04-03T10:05:00Z",
            channel="whatsapp",
            message_sent="actually can you answer here instead?",
            reply_sent="Sure thing!",
            topic_detected="general",
            sentiment_score=0.1,
            escalated=False,
            resolved=False,
        ))
        assert session.channel_switched
        assert set(session.channel_history) == {"email", "whatsapp"}

    def test_sentiment_track_records_each_turn(self):
        session = ConversationSession(
            session_id="S-002",
            customer_email="bob@example.com",
            customer_name="Bob",
            original_channel="email",
            current_channel="email",
        )
        for score in [0.0, -0.4, -0.8, 0.2]:
            session.add_turn(ConversationTurn(
                timestamp="2026-04-03T10:00:00Z",
                channel="email",
                message_sent="msg",
                reply_sent="reply",
                topic_detected="billing",
                sentiment_score=score,
                escalated=False,
                resolved=False,
            ))
        assert session.sentiment_track == [0.0, -0.4, -0.8, 0.2]
        expected_avg = (0.0 + -0.4 + -0.8 + 0.2) / 4
        assert abs(session.avg_sentiment - expected_avg) < 0.001

    def test_sentiment_trend_improving(self):
        session = ConversationSession(
            session_id="S-003",
            customer_email="charlie@example.com",
            customer_name="Charlie",
            original_channel="email",
            current_channel="email",
        )
        for score in [-0.8, -0.6, 0.3, 0.5]:
            session.add_turn(ConversationTurn(
                timestamp="2026-04-03T10:00:00Z",
                channel="email",
                message_sent="msg",
                reply_sent="reply",
                topic_detected="login",
                sentiment_score=score,
                escalated=False,
                resolved=False,
            ))
        assert session.sentiment_trend > 0

    def test_sentiment_trend_worsening(self):
        session = ConversationSession(
            session_id="S-004",
            customer_email="dave@example.com",
            customer_name="Dave",
            original_channel="whatsapp",
            current_channel="whatsapp",
        )
        for score in [0.2, 0.0, -0.6, -0.9]:
            session.add_turn(ConversationTurn(
                timestamp="2026-04-03T10:00:00Z",
                channel="whatsapp",
                message_sent="msg",
                reply_sent="reply",
                topic_detected="billing",
                sentiment_score=score,
                escalated=False,
                resolved=False,
            ))
        assert session.sentiment_trend < 0

    def test_topic_tracking_unique(self):
        session = ConversationSession(
            session_id="S-005",
            customer_email="eve@example.com",
            customer_name="Eve",
            original_channel="email",
            current_channel="email",
        )
        for topic in ["automations", "billing", "automations", "login"]:
            session.add_turn(ConversationTurn(
                timestamp="2026-04-03T10:00:00Z",
                channel="email",
                message_sent="msg",
                reply_sent="reply",
                topic_detected=topic,
                sentiment_score=0.0,
                escalated=False,
                resolved=False,
            ))
        assert session.topic_history == ["automations", "billing", "login"]

    def test_resolution_tracking(self):
        session = ConversationSession(
            session_id="S-006",
            customer_email="frank@example.com",
            customer_name="Frank",
            original_channel="email",
            current_channel="email",
        )
        session.add_turn(ConversationTurn(
            timestamp="2026-04-03T10:00:00Z",
            channel="email",
            message_sent="Help with Jira",
            reply_sent="Try reconnecting.",
            topic_detected="integrations",
            sentiment_score=-0.4,
            escalated=False,
            resolved=False,
        ))
        assert session.resolved is False

        session.add_turn(ConversationTurn(
            timestamp="2026-04-03T10:05:00Z",
            channel="email",
            message_sent="That worked, thanks!",
            reply_sent="Great, glad to help!",
            topic_detected="integrations",
            sentiment_score=0.5,
            escalated=False,
            resolved=True,
        ))
        assert session.resolved is True

    def test_escalation_tracking(self):
        session = ConversationSession(
            session_id="S-007",
            customer_email="grace@example.com",
            customer_name="Grace",
            original_channel="email",
            current_channel="email",
        )
        session.add_turn(ConversationTurn(
            timestamp="2026-04-03T10:00:00Z",
            channel="email",
            message_sent="I want a refund for the double charge.",
            reply_sent="I have escalated your case.",
            topic_detected="billing",
            sentiment_score=-0.8,
            escalated=True,
            resolved=False,
        ))
        assert session.escalated is True

    def test_close_session(self):
        session = ConversationSession(
            session_id="S-008",
            customer_email="henry@example.com",
            customer_name="Henry",
            original_channel="whatsapp",
            current_channel="whatsapp",
        )
        session.close("Resolved Jira sync issue via documented fix.")
        assert session.resolved is True
        assert session.summary == "Resolved Jira sync issue via documented fix."


# =====================================================================
# ConversationMemory Manager
# =====================================================================

class TestConversationMemory:
    """Tests for the ConversationMemory manager."""

    def test_create_profile(self):
        memory = ConversationMemory()
        profile = memory.get_or_create_profile(
            email="alice@example.com",
            name="Alice Martin",
            company="SmallBiz",
            plan="starter",
        )
        assert profile.customer_name == "Alice Martin"
        assert profile.company == "SmallBiz"
        assert profile.plan == "starter"

    def test_profile_persistence(self):
        memory = ConversationMemory()
        p1 = memory.get_or_create_profile("bob@example.com", "Bob", plan="free")
        p2 = memory.get_profile("bob@example.com")
        assert p1 is p2
        assert p2.customer_name == "Bob"

    def test_profile_update(self):
        memory = ConversationMemory()
        memory.get_or_create_profile("carol@example.com", "Carol", plan="free")
        profile = memory.get_or_create_profile("carol@example.com", "Carol Updated", plan="starter")
        assert profile.customer_name == "Carol Updated"
        assert profile.plan == "starter"

    def test_create_session(self):
        memory = ConversationMemory()
        memory.get_or_create_profile("dave@example.com", "Dave")
        session = memory.create_session("dave@example.com", "email", "Dave")
        assert session.customer_email == "dave@example.com"
        assert session.original_channel == "email"

    def test_get_active_session(self):
        memory = ConversationMemory()
        memory.get_or_create_profile("eve@example.com", "Eve")
        session = memory.create_session("eve@example.com", "whatsapp", "Eve")
        retrieved = memory.get_active_session("eve@example.com")
        assert retrieved.session_id == session.session_id

    def test_timed_out_session_moves_to_history(self):
        memory = ConversationMemory()
        memory.get_or_create_profile("frank@example.com", "Frank")
        old_session = memory.create_session("frank@example.com", "email", "Frank")
        old_session.last_activity = old_session.started_at - SESSION_TIMEOUT - timedelta(minutes=1)

        retrieved = memory.get_active_session("frank@example.com")
        assert retrieved is None

        history = memory.get_customer_history("frank@example.com")
        assert len(history) == 1
        assert history[0] is old_session

    def test_new_session_archives_old(self):
        memory = ConversationMemory()
        memory.get_or_create_profile("grace@example.com", "Grace")
        s1 = memory.create_session("grace@example.com", "email", "Grace")
        s2 = memory.create_session("grace@example.com", "whatsapp", "Grace")

        history = memory.get_customer_history("grace@example.com")
        assert len(history) == 1
        assert history[0] is s1

        active = memory.get_active_session("grace@example.com")
        assert active.session_id == s2.session_id

    def test_customer_stats_update(self):
        memory = ConversationMemory()
        memory.get_or_create_profile("henry@example.com", "Henry")
        session = memory.create_session("henry@example.com", "email", "Henry")

        memory.record_turn(
            session,
            message_body="Help needed",
            reply_body="Here is the answer",
            channel="email",
            topic="billing",
            sentiment=0.0,
            escalated=False,
            resolved=True,
        )

        profile = memory.get_profile("henry@example.com")
        assert profile.resolutions_total == 1
        assert profile.total_tickets == 1

    def test_turn_history_accessible(self):
        memory = ConversationMemory()
        memory.get_or_create_profile("iris@example.com", "Iris")
        session = memory.create_session("iris@example.com", "email", "Iris")

        memory.record_turn(session, "msg1", "reply1", "email", "general", 0.0, False, False)
        memory.record_turn(session, "msg2", "reply2", "email", "billing", -0.2, False, True)

        turns = memory.get_turn_history(session)
        assert len(turns) == 2
        assert turns[0].topic_detected == "general"
        assert turns[1].topic_detected == "billing"


# =====================================================================
# Integration: process_ticket with conversation memory
# =====================================================================

class TestMemoryIntegrated:
    """End-to-end: conversation memory integrated with process_ticket."""

    def test_followup_uses_session_context(self):
        from src.core_loop_prototype import process_ticket, IncomingMessage

        memory = ConversationMemory()
        memory.get_or_create_profile("alice@example.com", "Alice", plan="pro")
        session = memory.create_session("alice@example.com", "email", "Alice")

        msg1 = IncomingMessage(
            channel="email",
            body="How do I set up Jira integration?",
            sender_name="Alice",
            sender_email="alice@example.com",
        )
        result1 = process_ticket(msg1, customer_plan="pro", memory=memory)

        turns = memory.get_turn_history(session)
        assert len(turns) == 1
        assert turns[0].topic_detected == "integrations"

    def test_followup_sentiment_tracked(self):
        from src.core_loop_prototype import process_ticket, IncomingMessage

        memory = ConversationMemory()
        memory.get_or_create_profile("bob@example.com", "Bob", plan="free")
        session = memory.create_session("bob@example.com", "whatsapp", "Bob")

        msg1 = IncomingMessage(
            channel="whatsapp",
            body="hey can I use automations on free plan?",
            sender_name="Bob",
            sender_email="bob@example.com",
        )
        result1 = process_ticket(msg1, customer_plan="free", memory=memory)

        msg2 = IncomingMessage(
            channel="whatsapp",
            body="thanks, that worked!",
            sender_name="Bob",
            sender_email="bob@example.com",
        )
        result2 = process_ticket(msg2, customer_plan="free", memory=memory)

        assert len(session.sentiment_track) == 2
        assert len(session.turns) == 2

    def test_channel_switch_tracked_in_session(self):
        from src.core_loop_prototype import process_ticket, IncomingMessage

        memory = ConversationMemory()
        memory.get_or_create_profile("carol@example.com", "Carol", plan="starter")
        session = memory.create_session("carol@example.com", "email", "Carol")

        msg1 = IncomingMessage(
            channel="email",
            body="My billing looks wrong",
            sender_name="Carol",
            sender_email="carol@example.com",
        )
        result1 = process_ticket(msg1, customer_plan="starter", memory=memory)

        msg2 = IncomingMessage(
            channel="whatsapp",
            body="hey still have the billing issue",
            sender_name="Carol",
            sender_email="carol@example.com",
        )
        result2 = process_ticket(msg2, customer_plan="starter", memory=memory)

        assert session.channel_switched
        assert len(session.channel_history) == 2

    def test_report_summary_includes_all_fields(self):
        from src.core_loop_prototype import process_ticket, IncomingMessage

        memory = ConversationMemory()
        memory.get_or_create_profile("dave@example.com", "Dave", plan="enterprise")
        session = memory.create_session("dave@example.com", "email", "Dave")

        msg = IncomingMessage(
            channel="email",
            body="Need help with SSO configuration",
            sender_name="Dave",
            sender_email="dave@example.com",
        )
        result = process_ticket(msg, customer_plan="enterprise", memory=memory)

        report = session.report_summary
        assert "session_id" in report
        assert "customer_email" in report
        assert "channels_used" in report
        assert "avg_sentiment" in report
        assert "sentiment_trend" in report
        assert "resolved" in report
        assert "escalated" in report
        assert "topics" in report

    def test_escalation_marks_session_escalated(self):
        from src.core_loop_prototype import process_ticket, IncomingMessage

        memory = ConversationMemory()
        memory.get_or_create_profile("eve@example.com", "Eve", plan="starter")
        session = memory.create_session("eve@example.com", "email", "Eve")

        msg = IncomingMessage(
            channel="email",
            body="I was double charged last month. I need a refund immediately.",
            sender_name="Eve",
            sender_email="eve@example.com",
        )
        result = process_ticket(msg, customer_plan="starter", memory=memory)

        assert session.escalated is True
        assert result.escalated is True
        assert result.escalation_queue == "billing-team"

    def test_customer_profile_updated_across_turns(self):
        from src.core_loop_prototype import process_ticket, IncomingMessage

        memory = ConversationMemory()
        memory.get_or_create_profile("frank@example.com", "Frank", plan="free")
        memory.create_session("frank@example.com", "whatsapp", "Frank")

        msg = IncomingMessage(
            channel="whatsapp",
            body="hey need help with password reset",
            sender_name="Frank",
            sender_email="frank@example.com",
        )
        result = process_ticket(msg, customer_plan="free", memory=memory)

        profile = memory.get_profile("frank@example.com")
        assert profile.total_tickets == 1
        assert profile.resolutions_total == 1

    def test_session_with_no_active_returns_none(self):
        memory = ConversationMemory()
        result = memory.get_active_session("nonexistent@example.com")
        assert result is None

    def test_get_customer_history_empty_for_new_customer(self):
        memory = ConversationMemory()
        history = memory.get_customer_history("new@example.com")
        assert history == []
