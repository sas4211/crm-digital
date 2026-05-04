"""
CRM Gemini Gems — specialised AI personas for CRM workflows.

Each Gem wraps a Gemini model instance with a fixed system prompt.
Gems process NotebookLM-generated content and return structured JSON
ready for writing back to CRM records.

Usage:
    from src.gems.crm_gems import DealAnalystGem, CustomerResearcherGem

    gem = DealAnalystGem()
    result = gem.run(brief_text)
    print(result["risk_level"])  # "Medium"
"""

import json
import os
from google import genai
from google.genai import types
from src.gems.definitions import (
    DEAL_ANALYST,
    CUSTOMER_RESEARCHER,
    SALES_COACH,
    OBJECTION_HANDLER,
    ONBOARDING_TRAINER,
)


class _BaseGem:
    """Base class for all CRM Gems."""

    _system_prompt: str = ""
    _model_name: str = "gemini-1.5-pro"

    def __init__(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment.")
        self._client = genai.Client(api_key=api_key)

    def run(self, user_input: str) -> dict:
        """Send input to the Gem and return parsed JSON response."""
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=user_input,
            config=types.GenerateContentConfig(system_instruction=self._system_prompt),
        )
        raw = (response.text or "").strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    def run_with_context(self, context: str, question: str) -> dict:
        """Two-part input: rich context block + a focused question."""
        prompt = f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"
        return self.run(prompt)


class DealAnalystGem(_BaseGem):
    """
    Analyses NotebookLM deal briefs and returns structured deal intelligence.

    Input:  Full text of a NotebookLM briefing-doc report.
    Output: risk_level, next_actions, deal_score, buying_signals, blockers.

    Example:
        gem = DealAnalystGem()
        brief = open("output/acme-brief.md").read()
        analysis = gem.run(brief)
        # analysis["deal_score"] → 72
    """
    _system_prompt = DEAL_ANALYST


class CustomerResearcherGem(_BaseGem):
    """
    Surfaces pre-call customer intelligence from NotebookLM source content.

    Input:  NotebookLM ask() response or source fulltext about a company.
    Output: pain_points, talking_points, questions_to_ask, industry, size.

    Example:
        gem = CustomerResearcherGem()
        research = gem.run(notebooklm_ask_response)
        # research["pain_points"] → ["Slow procurement...", ...]
    """
    _system_prompt = CUSTOMER_RESEARCHER


class SalesCoachGem(_BaseGem):
    """
    Reviews deal history and delivers personalised rep coaching.

    Input:  Deal notes, call summaries, pipeline stage context.
    Output: coaching_summary, recommended_play, talk_track, urgency_rating.

    Example:
        gem = SalesCoachGem()
        coaching = gem.run(deal_notes_text)
        # coaching["recommended_play"] → "Schedule exec sponsor meeting"
    """
    _system_prompt = SALES_COACH


class ObjectionHandlerGem(_BaseGem):
    """
    Returns multi-approach responses to a customer objection.

    Input:  Objection text + optional deal context.
    Output: objection_type, root_cause, 3 scripted responses, follow_up_question.

    Example:
        gem = ObjectionHandlerGem()
        result = gem.run_with_context(
            context="Enterprise SaaS deal, $120k ACV, competitor is Salesforce",
            question="The customer said: 'Your price is too high.'"
        )
    """
    _system_prompt = OBJECTION_HANDLER


class OnboardingTrainerGem(_BaseGem):
    """
    Converts NotebookLM quiz/flashcard content into a structured onboarding plan.

    Input:  NotebookLM quiz JSON or flashcard markdown.
    Output: module_title, learning_objectives, sessions, completion_criteria.

    Example:
        gem = OnboardingTrainerGem()
        quiz_md = open("output/acme-quiz.md").read()
        plan = gem.run(quiz_md)
        # plan["sessions"][0]["title"] → "Product Fundamentals"
    """
    _system_prompt = ONBOARDING_TRAINER


# Gem registry — maps CRM use-case names to Gem classes
GEM_REGISTRY: dict[str, type[_BaseGem]] = {
    "deal_analyst": DealAnalystGem,
    "customer_researcher": CustomerResearcherGem,
    "sales_coach": SalesCoachGem,
    "objection_handler": ObjectionHandlerGem,
    "onboarding_trainer": OnboardingTrainerGem,
}


def get_gem(name: str) -> _BaseGem:
    """Instantiate a Gem by registry name."""
    cls = GEM_REGISTRY.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown Gem '{name}'. Available: {list(GEM_REGISTRY.keys())}"
        )
    return cls()
