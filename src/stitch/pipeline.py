"""
Stitch Pipeline — CRM Digital

Orchestrates the full enrichment flow:
  CRM record → NotebookLM notebook → Gemini Gem → Claude summary → CRM write-back

Typical usage:
    from src.stitch.pipeline import enrich_customer

    result = enrich_customer(
        customer_name="Acme Corp",
        website="https://acme.com",
        files=["./docs/acme-contract.pdf"],
        objection="Your price is too high.",
    )
    # result contains: notebook_id, brief_path, deal_analysis,
    #                  customer_research, objection_responses, claude_note
"""

import json
import os
import subprocess
from pathlib import Path

import anthropic

from src.gems.crm_gems import (
    CustomerResearcherGem,
    DealAnalystGem,
    ObjectionHandlerGem,
)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# NotebookLM helpers
# ---------------------------------------------------------------------------

def _nlm(args: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    """Run a notebooklm CLI command."""
    cmd = ["notebooklm"] + args
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=False,
    )


def provision_notebook(customer_name: str, website: str, files: list[str]) -> str:
    """
    Create a NotebookLM notebook for a customer, add sources, and return notebook_id.
    Raises RuntimeError if creation fails.
    """
    result = _nlm(["create", f"CRM: {customer_name}", "--json"])
    if result.returncode != 0:
        raise RuntimeError(f"notebooklm create failed: {result.stderr}")
    notebook_id: str = json.loads(result.stdout)["id"]

    if website:
        _nlm(["source", "add", website, "--notebook", notebook_id])

    for f in files:
        _nlm(["source", "add", f, "--notebook", notebook_id])

    return notebook_id


def generate_brief(notebook_id: str, customer_slug: str) -> Path:
    """
    Generate a briefing-doc report and download it. Returns the local file path.
    Blocks until the artifact is ready (uses artifact wait in a subprocess).
    """
    brief_path = OUTPUT_DIR / f"{customer_slug}-brief.md"

    # Kick off generation
    gen = _nlm([
        "generate", "report",
        "--format", "briefing-doc",
        "--notebook", notebook_id,
        "--json",
    ])
    if gen.returncode != 0:
        raise RuntimeError(f"notebooklm generate report failed: {gen.stderr}")

    artifact_id: str = json.loads(gen.stdout).get("task_id", "")

    # Wait for completion (up to 15 min)
    if artifact_id:
        _nlm(["artifact", "wait", artifact_id, "-n", notebook_id, "--timeout", "900"])

    # Download
    dl = _nlm([
        "download", "report", str(brief_path),
        "--notebook", notebook_id,
    ] + (["-a", artifact_id] if artifact_id else []))

    if dl.returncode != 0:
        raise RuntimeError(f"notebooklm download failed: {dl.stderr}")

    return brief_path


def ask_notebook(notebook_id: str, question: str) -> str:
    """Ask a question against the notebook and return the plain-text answer."""
    result = _nlm(["ask", question, "--notebook", notebook_id, "--json"])
    if result.returncode != 0:
        return ""
    return json.loads(result.stdout).get("answer", "")


def generate_quiz(notebook_id: str, customer_slug: str) -> Path:
    """Generate a quiz and download as markdown. Returns the local file path."""
    quiz_path = OUTPUT_DIR / f"{customer_slug}-quiz.md"
    _nlm(["generate", "quiz", "--notebook", notebook_id])
    _nlm([
        "download", "quiz", "--format", "markdown", str(quiz_path),
        "--notebook", notebook_id,
    ])
    return quiz_path


# ---------------------------------------------------------------------------
# Claude write-back helper
# ---------------------------------------------------------------------------

def _claude_crm_note(analysis: dict, research: dict) -> str:
    """
    Use Claude to produce a single CRM note from Gem outputs.
    Returns a concise, formatted note string.
    """
    client = anthropic.Anthropic()
    prompt = f"""You are a CRM assistant. Write a concise CRM note (max 120 words)
for a sales rep, combining the following two AI analyses. Use plain text, no JSON.

Deal Analysis:
{json.dumps(analysis, indent=2)}

Customer Research:
{json.dumps(research, indent=2)}

Format:
**Summary:** <2 sentences>
**Risk:** <level + 1 reason>
**Next Actions:** <numbered list, max 3>
**Talking Points:** <bullet list, max 3>
"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ---------------------------------------------------------------------------
# Main enrichment entry point
# ---------------------------------------------------------------------------

def enrich_customer(
    customer_name: str,
    website: str = "",
    files: list[str] | None = None,
    objection: str = "",
    generate_audio: bool = False,
) -> dict:
    """
    Full enrichment pipeline for a CRM customer record.

    Args:
        customer_name:  Display name (e.g. "Acme Corp")
        website:        Company URL to add as a NotebookLM source
        files:          List of local file paths (PDFs, docs) to add as sources
        objection:      Optional objection text to run through ObjectionHandlerGem
        generate_audio: If True, also generate a training podcast (slow)

    Returns:
        {
            "notebook_id": str,
            "brief_path": str,
            "deal_analysis": dict,       # DealAnalystGem output
            "customer_research": dict,   # CustomerResearcherGem output
            "objection_responses": dict, # ObjectionHandlerGem output (if provided)
            "claude_note": str,          # Claude-written CRM note
        }
    """
    files = files or []
    slug = customer_name.lower().replace(" ", "-")

    # Step 1 — provision notebook
    print(f"[stitch] Creating NotebookLM notebook for '{customer_name}'...")
    notebook_id = provision_notebook(customer_name, website, files)
    print(f"[stitch] Notebook ID: {notebook_id}")

    # Step 2 — ask for customer overview (feeds CustomerResearcherGem)
    print("[stitch] Querying notebook for customer overview...")
    overview = ask_notebook(
        notebook_id,
        "Summarise the company's main pain points, goals, and why they might buy.",
    )

    # Step 3 — generate deal brief (feeds DealAnalystGem)
    print("[stitch] Generating deal brief...")
    brief_path = generate_brief(notebook_id, slug)
    brief_text = brief_path.read_text(encoding="utf-8")

    # Step 4 — run Gems
    print("[stitch] Running DealAnalystGem...")
    deal_analysis = DealAnalystGem().run(brief_text)

    print("[stitch] Running CustomerResearcherGem...")
    customer_research = CustomerResearcherGem().run(overview or brief_text)

    objection_responses: dict = {}
    if objection:
        print("[stitch] Running ObjectionHandlerGem...")
        objection_responses = ObjectionHandlerGem().run_with_context(
            context=brief_text, question=objection
        )

    # Step 5 — Claude write-back note
    print("[stitch] Generating CRM note with Claude...")
    claude_note = _claude_crm_note(deal_analysis, customer_research)

    # Step 6 — optional podcast
    if generate_audio:
        print("[stitch] Generating training podcast (fire-and-forget)...")
        _nlm([
            "generate", "audio",
            f"Prepare the sales team for the {customer_name} deal",
            "--notebook", notebook_id,
        ])

    print("[stitch] Enrichment complete.")
    return {
        "notebook_id": notebook_id,
        "brief_path": str(brief_path),
        "deal_analysis": deal_analysis,
        "customer_research": customer_research,
        "objection_responses": objection_responses,
        "claude_note": claude_note,
    }
