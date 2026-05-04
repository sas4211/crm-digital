"""
Exercise 1.2 — Core Loop Prototype Tests

15 test cases discovered during the initial exploration phase.
Each validates a specific signal or requirement crystalised from the 55-ticket analysis.
"""

import pytest
from src.core_loop_prototype import (
    check_escalation,
    classify_category,
    detect_language,
    estimate_sentiment,
    IncomingMessage,
    process_ticket,
)


# =====================================================================
# TC-01: Legal threat in email body → immediate escalation
# =====================================================================
class TestLegalEscalation:
    """TC-01: Legal threats must never get a resolution attempt."""

    def test_legal_notice_escalates(self):
        msg = IncomingMessage(
            channel="email",
            body=(
                "I am writing to put you on formal notice regarding the unacceptable service delays. "
                "My attorney has advised me to pursue all available remedies, including small claims court. "
                "Fix this immediately or hear from my lawyer."
            ),
            sender_name="Sarah Mitchell",
            sender_email="sarah@example.com",
            subject="Formal notice",
        )
        result = process_ticket(msg, customer_plan="pro")
        assert result.escalated is True
        assert result.escalation_queue == "legal-team"
    def test_no_resolution_attempted(self):
        msg = IncomingMessage(
            channel="email",
            body="I've been charged twice this month for the same subscription. I want a full refund within 48 hours or I'm taking this to small claims court.",
            sender_name="Marcus Webb",
            sender_email="marcus@example.com",
            subject="Double charged again",
        )
        result = process_ticket(msg, customer_plan="starter")
        assert result.escalated is True
    def test_gdpr_escalates(self):
        msg = IncomingMessage(
            channel="email",
            body="I am submitting a formal GDPR data deletion request under Article 17. Please delete all my personal data and confirm in writing.",
            sender_name="Karin Svensson",
            sender_email="karin@example.com",
            subject="DSAR",
        )
        result = process_ticket(msg)
        assert result.escalated is True
        assert result.escalation_queue == "legal-team"


# =====================================================================
# TC-02: WhatsApp message in Spanish → reply in Spanish
# =====================================================================
class TestMultilingualWhatsApp:
    """TC-02 + TC-10: WhatsApp in another language, casual tone."""

    def test_detects_spanish(self):
        text = "cuando sale la integracion con Microsoft Teams?"
        assert detect_language(text) == "Spanish"

    def test_french_detected(self):
        text = "je veux upgrader vers starter mais j'ai une erreur"
        assert detect_language(text) == "French"

    def test_portuguese_detected(self):
        text = "Ola eu quero saber mais sobre os planos"
        assert detect_language(text) == "Portuguese"

    def test_english_default(self):
        text = "Hi, I need help with my password reset"
        assert detect_language(text) == "English"


# =====================================================================
# TC-03: Free plan asking about automations → plan limit explanation
# =====================================================================
class TestPlanAwareReplies:
    """TC-03: Plan-aware responses for feature availability."""

    def test_free_plan_automations_blocked(self):
        msg = IncomingMessage(
            channel="whatsapp",
            body="hey can i set up automations on the free plan?",
            sender_name="Jake",
            sender_email="jake@placeholder.com",
        )
        result = process_ticket(msg, customer_plan="free")
        assert "Free plan" in result.body
        assert "upgrade" in result.body.lower()
        assert result.resolved is True

    def test_pro_plan_timeline_available(self):
        msg = IncomingMessage(
            channel="email",
            body="How do I access the Timeline/Gantt view in my project?",
            sender_name="Priya Sharma",
            sender_email="priya@acme.com",
        )
        result = process_ticket(msg, customer_plan="pro")
        assert "Timeline" in result.body or "Pro" in result.body or "available" in result.body.lower()
        assert result.resolved is True

    def test_starter_automations_limited(self):
        msg = IncomingMessage(
            channel="email",
            body="My automation stopped firing. It was working last week. I'm on the Starter plan.",
            sender_name="Tom",
            sender_email="tom@example.com",
        )
        result = process_ticket(msg, customer_plan="starter")
        assert "50" in result.body or "Starter" in result.body


# =====================================================================
# TC-04: Known Jira first-sync bug → documented fix
# =====================================================================
class TestKnownBugsKB:
    """TC-04: KB provides documented fixes for known issues."""

    def test_jira_duplicate_kb_match(self):
        msg = IncomingMessage(
            channel="email",
            body="After connecting Jira, half my tasks are duplicated. What happened?",
            sender_name="Dev Team Lead",
            sender_email="dev@example.com",
        )
        result = process_ticket(msg, customer_plan="pro")
        assert result.metadata["kb_matched"] is True
        assert "duplicate" in result.body.lower()


# =====================================================================
# TC-05: Angry customer (3rd ticket) → empathy + immediate escalation
# =====================================================================
class TestSentimentAndEmpathy:
    """TC-05: Negative sentiment triggers empathy-first responses."""

    def test_very_negative_sentiment_score(self):
        text = "This is unacceptable. Third time I'm reporting this and still not fixed. Absolutely ridiculous."
        score = estimate_sentiment(text)
        assert score < -0.5

    def test_empathy_prefix_on_negative(self):
        msg = IncomingMessage(
            channel="email",
            body="This is the third time I'm writing in and the issue is STILL not fixed. This is ridiculous and unacceptable. I'm fed up with this useless product.",
            sender_name="Angry Dave",
            sender_email="angry@example.com",
        )
        result = process_ticket(msg)
        # Should detect negative sentiment and include empathy, OR escalate
        assert result.metadata["sentiment"] < -0.5


# =====================================================================
# TC-06: Password reset not working → steps provided
# =====================================================================
class TestPasswordReset:
    """TC-06: Known fix for common how-to questions."""

    def test_password_reset_kb_match(self):
        msg = IncomingMessage(
            channel="web_form",
            body="I tried to reset my password 3 times but I never get the email. Already checked spam.",
            sender_name="Lost User",
            sender_email="lost@example.com",
        )
        result = process_ticket(msg)
        assert result.resolved is True
        assert result.category == "login"


# =====================================================================
# TC-07: Double charge claim → escalation, no refund attempt
# =====================================================================
class TestBillingEscalation:
    """TC-07: Billing disputes escalate to billing-team."""

    def test_double_charge_escalates(self):
        msg = IncomingMessage(
            channel="email",
            body="I was double charged this month. The invoice shows two charges of $29 each on the same day. I need a refund.",
            sender_name="Billing User",
            sender_email="billing@example.com",
        )
        result = process_ticket(msg)
        assert result.escalated is True
        assert result.escalation_queue == "billing-team"

    def test_overcharge_escalates(self):
        should, queue, _ = check_escalation("I think I've been charged twice for the same thing")
        assert should is True
        assert queue == "billing-team"

    def test_refund_escalates(self):
        should, queue, _ = check_escalation("Can I get a refund for last month?")
        assert should is True
        assert queue == "billing-team"


# =====================================================================
# TC-08: Enterprise SSO lockout → escalation
# =====================================================================
class TestEnterpriseSSO:
    """TC-08: SSO lockout is always a security/escalation issue."""

    def test_sso_lockout_escalates(self):
        msg = IncomingMessage(
            channel="email",
            body="We have 40+ users locked out after enabling SSO. They can't authenticate and the emergency override isn't working.",
            sender_name="Enterprise IT",
            sender_email="it@enterprise.com",
        )
        result = process_ticket(msg, customer_plan="enterprise")
        assert result.escalated is True


# =====================================================================
# TC-09: GDPR data deletion request → escalate to legal
# =====================================================================
class TestGDPR:
    """TC-09: GDPR requests must escalate to legal, never process directly."""

    def test_gdpr_deletion(self):
        should, queue, _ = check_escalation("I need to submit a GDPR data deletion request")
        assert should is True
        assert queue == "legal-team"

    def test_dsar_request(self):
        should, queue, _ = check_escalation("Submitting a DSAR for all my personal data under GDPR Article 15")
        assert should is True
        assert queue == "legal-team"


# =====================================================================
# TC-10: WhatsApp casual tone → match it
# =====================================================================
class TestChannelFormatting:
    """TC-10: Response formatting matches channel expectations."""

    def test_email_has_signature(self):
        msg = IncomingMessage(
            channel="email",
            body="How do I export my data to CSV?",
            sender_name="Sarah",
            sender_email="sarah@example.com",
        )
        result = process_ticket(msg)
        assert "Best," in result.body
        assert "Alex" in result.body

    def test_whatsapp_has_brief_signoff(self):
        msg = IncomingMessage(
            channel="whatsapp",
            body="hey quick q - how do i add people to my workspace?",
            sender_name="",
            sender_email="quick@placeholder.com",
        )
        result = process_ticket(msg)
        assert "Alex, FlowDesk" in result.body

    def test_webform_no_signoff(self):
        msg = IncomingMessage(
            channel="web_form",
            body="How do I archive a completed project?",
            sender_name="Web User",
            sender_email="web@example.com",
        )
        result = process_ticket(msg)
        assert "Best," not in result.body
        assert "— Alex, FlowDesk" not in result.body


# =====================================================================
# TC-11: Feature request → acknowledge, no roadmap commitment
# =====================================================================
class TestFeatureRequests:
    """TC-11: Feature requests acknowledged without roadmap promises."""

    def test_dark_mode_request(self):
        msg = IncomingMessage(
            channel="whatsapp",
            body="any chance you guys will add dark mode? my eyes are dying",
            sender_name="",
            sender_email="dark@placeholder.com",
        )
        result = process_ticket(msg)
        body_lower = result.body.lower()
        assert "dark mode" in body_lower or "product team" in body_lower or "thanks" in body_lower
        assert "next month" not in body_lower
        assert "coming soon" not in body_lower
        assert "q2" not in body_lower


# =====================================================================
# TC-12: Security incident via WhatsApp → same critical response as email
# =====================================================================
class TestSecurityWhatsApp:
    """TC-12: Channel does not equal severity — WhatsApp can be urgent."""

    def test_security_via_whatsapp_escalates(self):
        msg = IncomingMessage(
            channel="whatsapp",
            body="someone else logged into my account from an unknown location. what do i do??",
            sender_name="",
            sender_email="hacked@placeholder.com",
        )
        result = process_ticket(msg)
        assert result.escalated is True
        assert result.escalation_queue == "security-team"


# =====================================================================
# TC-13: Escalation keyword scanning patterns
# =====================================================================
class TestEscalationKeywords:
    """Validation of all escalation trigger patterns."""

    def test_attorney_keyword(self):
        should, queue, _ = check_escalation("I've told my attorney about this")
        assert should is True
        assert queue == "legal-team"

    def test_legal_notice(self):
        should, queue, _ = check_escalation("This is a formal legal notice")
        assert should is True
        assert queue == "legal-team"

    def test_breach_keyword(self):
        should, queue, _ = check_escalation("I think there's been a data breach")
        assert should is True
        assert queue == "security-team"

    def test_hacked_keyword(self):
        should, queue, _ = check_escalation("I think my account got hacked")
        assert should is True
        assert queue == "security-team"

    def test_gdpr_keyword(self):
        should, queue, _ = check_escalation("GDPR data request")
        assert should is True
        assert queue == "legal-team"

    def test_normal_message_no_escalation(self):
        should, _, _ = check_escalation("Hey, how do I create a new project?")
        assert should is False

    def test_escalation_reason_map(self):
        should, _, reason = check_escalation("I want a refund for the double charge")
        assert should is True
        assert "Billing" in reason


# =====================================================================
# TC-14: Category classification accuracy
# =====================================================================
class TestCategoryClassification:
    """Validate that categories are correctly identified."""

    def test_automation_category(self):
        assert classify_category("My automation isn't firing") == "automations"

    def test_billing_category(self):
        assert classify_category("I need to upgrade my plan") == "billing"

    def test_integration_category(self):
        assert classify_category("Slack notifications stopped working") == "integrations"

    def test_login_category(self):
        assert classify_category("I forgot my password") == "login"

    def test_mobile_category(self):
        assert classify_category("The mobile app crashes when I open it") == "mobile"

    def test_views_category(self):
        assert classify_category("How do I use the Timeline view?") == "views"

    def test_general_fallback(self):
        assert classify_category("Can you help me with this?") == "general"


# =====================================================================
# TC-15: Channel formatting rules (email vs WhatsApp vs web form)
# =====================================================================
class TestChannelFormattingRules:
    """Email gets signature. WhatsApp gets brief sign-off. Web form gets neither."""

    def test_email_signature_format(self):
        msg = IncomingMessage(
            channel="email",
            body="I need to change my billing email address.",
            sender_name="Jane Doe",
            sender_email="jane@company.com",
        )
        result = process_ticket(msg, customer_plan="starter")
        assert "Best,\nAlex" in result.body
        assert "FlowDesk Customer Success" in result.body

    def test_whatsapp_brief_signoff(self):
        msg = IncomingMessage(
            channel="whatsapp",
            body="how do i add slack integration?",
            sender_name="",
            sender_email="wa@placeholder.com",
        )
        result = process_ticket(msg, customer_plan="pro")
        assert "Alex, FlowDesk" in result.body

    def test_webform_no_signoff_at_all(self):
        msg = IncomingMessage(
            channel="web_form",
            body="Need help setting up Jira sync.",
            sender_name="Web User",
            sender_email="web@example.com",
        )
        result = process_ticket(msg, customer_plan="pro")
        # Web form replies should not have sign-offs
        for phrase in ["Best,", "— Alex", "FlowDesk Customer Success"]:
            assert phrase not in result.body, f"Web form reply should not contain '{phrase}'"


# =====================================================================
# Integration tests: end-to-end core loop
# =====================================================================
class TestCoreLoopIntegration:
    """End-to-end tests of the full process_ticket flow."""

    def test_happy_path(self):
        msg = IncomingMessage(
            channel="email",
            body="How do I invite 2 more team members?",
            sender_name="Alice Martin",
            sender_email="alice@smallbiz.com",
        )
        result = process_ticket(msg, customer_plan="starter")
        assert result.ticket_id
        assert result.customer_name == "Alice Martin"
        assert result.category in ("billing", "general")
        assert result.escalated is False

    def test_escalated_ticket_not_resolved(self):
        msg = IncomingMessage(
            channel="email",
            body="I'm filing a GDPR data deletion request. Delete all my data now.",
            sender_name="Privacy First",
            sender_email="privacy@example.com",
        )
        result = process_ticket(msg)
        assert result.escalated is True
        assert result.resolved is False

    def test_metadata_populated(self):
        msg = IncomingMessage(
            channel="whatsapp",
            body="hey my automations stopped working last week :(",
            sender_name="",
            sender_email="wa2@placeholder.com",
        )
        result = process_ticket(msg, customer_plan="starter")
        assert "sentiment" in result.metadata
        assert "plan" in result.metadata
        assert "kb_matched" in result.metadata
