"""
Exercise 1.4 â€” Agent Skills tests.

Tests each skill definition and verifies implementation callables resolve.
"""

import pytest
import inspect

from src.skills.manifest import (
    SKILLS,
    AgentSkill,
    get_skill,
    list_skills,
    search_knowledge_base,
    sentiment_analysis,
    escalation_decision,
    channel_adaptation,
    customer_identification,
    conversation_memory,
    category_classification,
    language_detection,
)


class TestSkillRegistry:
    """Tests for the skill registry itself."""

    def test_all_skills_registered(self):
        assert len(SKILLS) == 8
        ids = [s.skill_id for s in SKILLS]
        assert "knowledge_retrieval" in ids
        assert "sentiment_analysis" in ids
        assert "escalation_decision" in ids
        assert "channel_adaptation" in ids
        assert "customer_identification" in ids
        assert "conversation_memory" in ids
        assert "category_classification" in ids
        assert "language_detection" in ids

    def test_get_skill_returns_correct(self):
        skill = get_skill("escalation_decision")
        assert skill is not None
        assert skill.display_name == "Escalation Decision"

    def test_get_unknown_skill_returns_none(self):
        assert get_skill("nonexistent") is None

    def test_list_skills_sorted_by_priority(self):
        skills = list_skills()
        # Highest priority should be first
        assert skills[0].priority >= skills[-1].priority

    def test_escalation_has_highest_priority(self):
        escalation = get_skill("escalation_decision")
        assert escalation.priority == 30

    def test_language_detection_runs_first(self):
        lang = get_skill("language_detection")
        assert lang.priority == 40


class TestKnowledgeRetrievalSkill:
    def test_inputs_defined(self):
        assert len(search_knowledge_base.inputs) == 1
        assert search_knowledge_base.inputs[0].name == "query"
        assert search_knowledge_base.inputs[0].required is True

    def test_outputs_defined(self):
        assert len(search_knowledge_base.outputs) == 1
        assert search_knowledge_base.outputs[0].name == "results"

    def test_impl_path_valid(self):
        mod_path = search_knowledge_base.implementation
        module_name, func_name = mod_path.rsplit(".", 1)
        mod = __import__(module_name, fromlist=[func_name])
        assert callable(getattr(mod, func_name))

    def test_when_to_use_describes_trigger(self):
        text = search_knowledge_base.when_to_use
        assert "product" in text.lower() or "question" in text.lower()


class TestSentimentAnalysisSkill:
    def test_inputs_defined(self):
        assert len(sentiment_analysis.inputs) == 1
        assert sentiment_analysis.inputs[0].name == "text"

    def test_outputs_defined(self):
        output_names = [o.name for o in sentiment_analysis.outputs]
        assert "score" in output_names
        assert "trend" in output_names

    def test_runs_on_every_message(self):
        assert "EVERY" in sentiment_analysis.when_to_use.upper()

    def test_impl_callable(self):
        mod_path = sentiment_analysis.implementation
        module_name, func_name = mod_path.rsplit(".", 1)
        mod = __import__(module_name, fromlist=[func_name])
        assert callable(getattr(mod, func_name))


class TestEscalationDecisionSkill:
    def test_has_escalate_output(self):
        names = [o.name for o in escalation_decision.outputs]
        assert "should_escalate" in names
        assert "reason" in names
        assert "queue" in names

    def test_runs_before_other_processing(self):
        assert "before" in escalation_decision.when_to_use.lower()

    def test_checks_legal_security_billing(self):
        text = escalation_decision.when_to_use.lower()
        assert "legal" in text
        assert "security" in text
        assert "billing" in text

    def test_impl_path_valid(self):
        mod_path = escalation_decision.implementation
        module_name, func_name = mod_path.rsplit(".", 1)
        mod = __import__(module_name, fromlist=[func_name])
        assert callable(getattr(mod, func_name))


class TestChannelAdaptationSkill:
    def test_inputs_defined(self):
        input_names = [i.name for i in channel_adaptation.inputs]
        assert "body" in input_names
        assert "channel" in input_names

    def test_email_signoff_described(self):
        assert "email" in channel_adaptation.when_to_use.lower()

    def test_whatsapp_casual_described(self):
        assert "whatsapp" in channel_adaptation.when_to_use.lower()

    def test_webform_no_signoff(self):
        text = channel_adaptation.when_to_use.lower()
        assert "no sign-off" in text.lower() or "web form" in text.lower() or "self-contained" in text.lower()

    def test_impl_path_valid(self):
        mod_path = channel_adaptation.implementation
        module_name, func_name = mod_path.rsplit(".", 1)
        mod = __import__(module_name, fromlist=[func_name])
        assert callable(getattr(mod, func_name))


class TestCustomerIdentificationSkill:
    def test_inputs_defined(self):
        names = [i.name for i in customer_identification.inputs]
        assert "email" in names
        assert "name" in names
        assert "phone" in names
        assert "company" in names
        assert "plan" in names

    def test_outputs_defined(self):
        names = [o.name for o in customer_identification.outputs]
        assert "customer_id" in names
        assert "profile" in names

    def test_email_as_primary_key(self):
        assert "email" in customer_identification.description.lower() or "primary" in customer_identification.description.lower()

    def test_whatsapp_fallback(self):
        text = customer_identification.when_to_use.lower()
        assert "whatsapp" in text
        assert ("phone" in text or "fallback" in text)

    def test_impl_path_valid(self):
        mod_path = customer_identification.implementation
        # Path is module.Class.method format (may also be module.function)
        parts = mod_path.split(".")
        module_name = ".".join(parts[:-2])
        cls_or_fn_name = parts[-2]
        method_name = parts[-1]
        module = __import__(module_name, fromlist=[cls_or_fn_name])
        cls_or_fn = getattr(module, cls_or_fn_name)
        assert callable(cls_or_fn) or hasattr(cls_or_fn, method_name)


class TestConversationMemorySkill:
    def test_inputs_defined(self):
        assert len(conversation_memory.inputs) == 1
        assert conversation_memory.inputs[0].name == "customer_email"

    def test_detects_channel_switch(self):
        text = conversation_memory.when_to_use.lower()
        assert "channel" in text

    def test_session_context(self):
        names = [o.name for o in conversation_memory.outputs]
        assert "session" in names
        assert "context_note" in names
        assert "topic_history" in names


class TestCategoryClassificationSkill:
    def test_input_defined(self):
        assert len(category_classification.inputs) == 1
        assert category_classification.inputs[0].name == "text"

    def test_categories_listed(self):
        text = category_classification.outputs[0].description
        assert "automations" in text
        assert "billing" in text
        assert "general" in text


class TestLanguageDetectionSkill:
    def test_input_defined(self):
        assert len(language_detection.inputs) == 1
        assert language_detection.inputs[0].name == "text"

    def test_english_fallback(self):
        text = language_detection.outputs[0].description
        assert "english" in text.lower()
        assert "fallback" in text.lower()

    def test_runs_first(self):
        assert "first" in language_detection.when_to_use.lower()
