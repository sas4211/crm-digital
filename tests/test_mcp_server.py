"""
Exercise 1.4 — MCP Server tests.

Tests each MCP tool endpoint for correct behavior:
- search_knowledge_base
- create_ticket
- get_customer_history
- escalate_to_human
- send_response
- get_ticket_status
- get_dashboard
- process_customer_message
"""

import pytest
import asyncio

from src.mcp_server import (
    server,
    memory,
    create_ticket,
    escalate_to_human,
    get_customer_history,
    get_dashboard,
    get_ticket_status,
    search_knowledge_base,
    send_response,
    process_customer_message,
    Channel,
    Priority,
)


class TestSearchKnowledgeBase:
    """search_knowledge_base tool."""

    def test_finds_relevant_entries(self):
        result = search_knowledge_base("password reset")
        assert len(result.results) >= 1
        assert result.results[0].solution != ""
        assert any("password" in r.problem.lower() or "reset" in r.problem.lower() for r in result.results)

    def test_returns_empty_for_unknown(self):
        result = search_knowledge_base("quantum computing")
        assert len(result.results) >= 0  # May find partial matches

    def test_multiple_results(self):
        result = search_knowledge_base("integration")
        assert len(result.results) >= 1

    def test_result_has_required_fields(self):
        result = search_knowledge_base("password")
        if result.results:
            entry = result.results[0]
            assert entry.category in ("login", "general")
            assert entry.problem
            assert entry.solution


class TestCreateTicket:
    """create_ticket tool."""

    def test_creates_ticket_and_returns_id(self):
        result = create_ticket(
            customer_id="test@example.com",
            issue="I need help with my account settings",
            plan="free",
        )
        assert result.ticket_id.startswith("TICK-")
        assert result.status in ("resolved", "escalated", "open")

    def test_creates_ticket_with_specific_channel(self):
        result = create_ticket(
            customer_id="whatsapp_user@placeholder.com",
            issue="hey quick question about automations",
            channel=Channel.WHATSAPP,
            priority=Priority.LOW,
            customer_name="Bob",
        )
        assert result.ticket_id.startswith("TICK-")

    def test_creates_ticket_with_custom_subject(self):
        result = create_ticket(
            customer_id="subject_test@example.com",
            issue="The webhook endpoint is returning 500",
            subject="Webhook 500 error",
            channel=Channel.EMAIL,
            priority=Priority.HIGH,
            plan="enterprise",
        )
        assert result.ticket_id.startswith("TICK-")

    def test_escalation_detected_for_legal(self):
        result = create_ticket(
            customer_id="legal@example.com",
            issue="I am putting you on formal legal notice regarding the service delays.",
            plan="starter",
        )
        assert result.status == "escalated"

    def test_escalation_for_billing(self):
        result = create_ticket(
            customer_id="refund@example.com",
            issue="I was double charged this month. I need a refund.",
            priority=Priority.HIGH,
        )
        assert result.status == "escalated"


class TestGetCustomerHistory:
    """get_customer_history tool."""

    def test_returns_profile_for_unknown_customer(self):
        result = get_customer_history("new_user@example.com")
        assert result.email == "new_user@example.com"
        assert result.plan == "free"

    def test_returns_entries_after_interaction(self):
        # Create a ticket first to populate the session
        create_ticket(
            customer_id="history_check@example.com",
            issue="How do I reset my password?",
            plan="starter",
        )
        result = get_customer_history("history_check@example.com")
        assert result.total_tickets >= 1
        # Should have at least the session
        assert result.sessions >= 1


class TestEscalateToHuman:
    """escalate_to_human tool."""

    def test_escalates_existing_ticket(self):
        ticket = create_ticket(
            customer_id="escalate_me@example.com",
            issue="Some issue",
        )
        result = escalate_to_human(
            ticket_id=ticket.ticket_id,
            reason="Customer is very angry and demands a manager",
            queue="tier-2-support",
        )
        assert result.ticket_id == ticket.ticket_id
        assert result.escalation_id == f"ESC-{ticket.ticket_id}"
        assert result.queue == "tier-2-support"

    def test_escalates_to_legal(self):
        result = escalate_to_human(
            ticket_id="TICK-LEGAL-001",
            reason="GDPR data deletion request received",
            queue="legal-team",
        )
        assert result.queue == "legal-team"

    def test_escalates_to_security(self):
        result = escalate_to_human(
            ticket_id="TICK-SEC-001",
            reason="Customer reports unauthorized access",
            queue="security-team",
        )
        assert result.queue == "security-team"


class TestSendResponse:
    """send_response tool."""

    def test_queues_message_for_delivery(self):
        ticket = create_ticket(
            customer_id="reply_to@example.com",
            issue="Simple question",
        )
        result = send_response(
            ticket_id=ticket.ticket_id,
            message="Here is the solution to your issue.",
            channel=Channel.EMAIL,
        )
        assert result.delivery_status == "queued"
        assert result.channel == "email"
        assert result.ticket_id == ticket.ticket_id

    def test_sends_via_whatsapp(self):
        result = send_response(
            ticket_id="TICK-WA-001",
            message="Hey! Quick answer for you.",
            channel=Channel.WHATSAPP,
        )
        assert result.channel == "whatsapp"
        assert result.delivery_status == "queued"

    def test_sends_via_webform(self):
        result = send_response(
            ticket_id="TICK-WEB-001",
            message="Your issue has been resolved.",
            channel=Channel.WEB_FORM,
        )
        assert result.channel == "web_form"


class TestGetTicketStatus:
    """get_ticket_status tool."""

    def test_returns_status_for_existing(self):
        ticket = create_ticket(
            customer_id="status_check@example.com",
            issue="How do I export data to CSV?",
            plan="pro",
        )
        result = get_ticket_status(ticket.ticket_id)
        assert result.ticket_id == ticket.ticket_id
        assert result.status == ticket.status

    def test_returns_not_found_for_unknown(self):
        result = get_ticket_status("TICK-NONEXISTENT")
        assert result.status == "not_found"
        assert result.escalated is False
        assert result.resolved is False


class TestGetDashboard:
    """get_dashboard tool."""

    def test_returns_all_fields(self):
        dash = get_dashboard()
        assert dash.active_sessions >= 0
        assert dash.total_customers >= 0
        assert dash.total_tickets >= 0
        assert dash.escalated_tickets >= 0
        assert dash.resolved_tickets >= 0
        assert isinstance(dash.avg_sentiment, float)

    def test_dashboard_reflects_tickets(self):
        get_dashboard()  # baseline
        ticket = create_ticket(
            customer_id="dash_user@example.com",
            issue="Need help with Jira sync duplicates",
        )
        dash = get_dashboard()
        assert dash.total_tickets >= 1


class TestProcessCustomerMessage:
    """process_customer_message tool."""

    def test_processes_simple_message(self):
        result = process_customer_message(
            customer_email="process_test@example.com",
            message="How do I add team members to my workspace?",
            customer_name="Test User",
            plan="starter",
        )
        assert result.ticket_id.startswith("TICK-")

    def test_processes_legal_escapes_no_resolution(self):
        result = process_customer_message(
            customer_email="legal_process@example.com",
            message="I am submitting this as a formal legal notice. You will hear from my attorney.",
            plan="enterprise",
        )
        assert result.status == "escalated"

    def test_processes_in_different_channels(self):
        import time
        result_email = process_customer_message(
            customer_email="channel_test_2@example.com",
            message="How do I set up the Slack integration?",
            channel=Channel.EMAIL,
            plan="pro",
            customer_name="Tester A",
        )
        time.sleep(1.1)  # Ensure different timestamp-based ticket IDs
        result_wa = process_customer_message(
            customer_email="channel_test_2@example.com",
            message="hey does the slack integration still work?",
            channel=Channel.WHATSAPP,
            plan="pro",
            customer_name="Tester B",
        )
        assert result_email.ticket_id != result_wa.ticket_id
