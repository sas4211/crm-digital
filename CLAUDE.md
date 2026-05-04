# CRM Digital — Claude Code Configuration

## Project Overview
CRM Digital is a customer relationship management platform integrating AI-powered research, note-taking, and content generation via Google NotebookLM and Claude.

## Tech Stack
- **Frontend:** TBD (React / Next.js recommended)
- **Backend:** TBD (Node.js / Python FastAPI recommended)
- **AI Layer:** Google NotebookLM (`notebooklm-py`) + Claude API
- **Data:** Customer records, interaction logs, AI-generated summaries

---

## Skills & Plugins

This project uses the following Claude Code skills (see `skill.md` for full reference):

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `notebooklm` | `/notebooklm` or intent detection | AI research, podcast, quiz, summaries |
| `frontend-design` | UI component requests | Production-grade React components |
| `claude-api` | Anthropic SDK usage | Claude-powered CRM features |
| `gstack` | `/office-hours`, `/qa`, `/ship`, etc. | Team roles, browser QA, deploy |
| `superpowers` | `/brainstorm`, `/debug`, `/tdd` | TDD enforcement, structured debugging |
| `gsd` | `/gsd-*` commands | Spec-driven dev, context rot prevention |

Plugin requirements are documented in `plugins/requirement.md`.

---

## NotebookLM Integration

The CRM uses Google NotebookLM to enrich customer and deal data with AI-generated content.

### Setup (one-time)
```bash
pip install notebooklm-py
notebooklm login          # Google OAuth — opens browser
notebooklm list           # Verify auth works
```

### Core Workflows

#### 1. Customer Research Notebook
Create a dedicated notebook per customer or deal:
```bash
notebooklm create "CRM: [Customer Name]"
notebooklm source add "https://customer-website.com"
notebooklm source add ./meeting-notes.pdf
notebooklm ask "Summarize their key pain points and buying signals"
```

#### 2. Generate Deal Brief
```bash
notebooklm generate report --format briefing-doc
notebooklm download report ./output/deal-brief.md
```

#### 3. Generate Training Podcast for Sales Team
```bash
notebooklm generate audio "Focus on objection handling and competitive positioning"
notebooklm download audio ./output/training.mp3
```

#### 4. Generate Flashcards / Quiz for Onboarding
```bash
notebooklm generate quiz --difficulty medium
notebooklm download quiz --format markdown ./output/onboarding-quiz.md
```

### Environment Variables
```env
NOTEBOOKLM_HOME=~/.notebooklm          # Default config dir
NOTEBOOKLM_AUTH_JSON=<json-string>     # CI/CD inline auth
```

---

## Stitch Architecture

The "stitch" layer connects CRM data → NotebookLM → Claude output:

```
CRM Data (contacts, deals, notes)
        │
        ▼
  NotebookLM Notebook (per customer / per deal)
  ├── Sources: website, PDFs, meeting notes, emails
  ├── Chat: AI Q&A on customer context
  └── Artifacts: briefs, podcasts, quizzes, flashcards
        │
        ▼
  Claude API (claude-sonnet-4-6)
  ├── Summarise artifact output
  ├── Write CRM notes back to records
  └── Suggest next actions
        │
        ▼
  CRM UI — displays enriched customer profile
```

---

## Claude Code Frameworks

Three development frameworks are active in this project. Install them once (see `plugins/requirement.md`), then use their slash commands in any session.

### gstack (Gary Tan — team roles & browser QA)
Role-based virtual team with 30+ slash commands. Provides planning reviews, design audits, browser-based QA, security audits, and shipping automation.

**Key commands for CRM work:**
| Command | Use |
|---------|-----|
| `/office-hours` | Product interrogation before building |
| `/autoplan` | CEO + design + eng review in one shot |
| `/plan-eng-review` | Lock architecture, data-flow diagrams |
| `/plan-design-review` | Design audit (rate 0–10) |
| `/qa` | Browser-based testing + bug fixes |
| `/cso` | OWASP Top 10 + STRIDE security audit |
| `/review` | Code review, auto-fix obvious bugs |
| `/ship` | Sync main → run tests → push → open PR |
| `/investigate` | Systematic root-cause debugging |
| `/browse` | Real Chromium browser (~100ms/cmd) |

Use `/browse` for all web browsing. Never use `mcp__claude-in-chrome__*` tools.

---

### Superpowers (Jesse Vincent — TDD & implementation discipline)
Enforces professional software development practices: test-driven development, structured debugging, and subagent-driven code review.

**Install:** `/plugin install superpowers@claude-plugins-official`

**Key commands:**
| Command | Use |
|---------|-----|
| `/brainstorm` | Socratic session to refine requirements before coding |
| `/write-plan` | Break work into 2–5 min atomic tasks with file paths |
| `/execute-plan` | Run batched plan with review checkpoints |
| `/test-driven-development` | RED → GREEN → REFACTOR cycle |
| `/debug` | Four-phase root-cause debugging methodology |

**Rule:** Always `/brainstorm` a CRM feature before implementing. Always write failing tests first.

---

### GSD — Get Stuff Done (Lex Christopherson — spec-driven, context rot prevention)
Solves context rot by spawning fresh Claude instances per task. Spec-driven workflow: discuss → plan → execute in parallel waves.

**Install:** `npx get-shit-done-cc --claude --local`

**Key commands:**
| Command | Use |
|---------|-----|
| `/gsd-new-project` | Capture idea → research → requirements → roadmap |
| `/gsd-discuss-phase` | Capture implementation decisions |
| `/gsd-plan-phase` | Research + plan + verify |
| `/gsd-execute-phase <N>` | Execute all plans in parallel waves |
| `/gsd-verify-work` | User acceptance testing |
| `/gsd-ship` | Create PR from verified work |
| `/gsd-next` | Auto-detect and run the next workflow step |
| `/gsd-fast <text>` | Inline trivial tasks, skip planning |
| `/gsd-pause-work` | Handoff when stopping (writes HANDOFF.json) |
| `/gsd-resume-work` | Restore from last session |

**State files:** `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `.planning/`

---

### Framework Interaction

```
New Feature Request
        │
        ├─► /brainstorm  (Superpowers) — refine requirements
        │
        ├─► /office-hours → /autoplan  (gstack) — CEO + eng + design review
        │
        ├─► /gsd-discuss-phase → /gsd-plan-phase  (GSD) — spec & atomic tasks
        │
        ├─► /test-driven-development  (Superpowers) — RED → GREEN → REFACTOR
        │
        ├─► /gsd-execute-phase  (GSD) — parallel execution in fresh contexts
        │
        ├─► /qa + /cso  (gstack) — browser QA + security audit
        │
        └─► /gsd-ship → /ship  (GSD + gstack) — verified PR + deploy
```

---

## Conventions

- Use `--json` flag on all `notebooklm` CLI calls when parsing output programmatically.
- Store notebook IDs in the CRM database (customer record → `notebooklm_notebook_id` field).
- For parallel agent workflows, always pass `-n <notebook_id>` explicitly; never rely on shared `use` context.
- All generated files go to `./output/` (gitignored).

## File Structure
```
crm-digital/
├── CLAUDE.md              ← this file
├── skill.md               ← skills reference
├── plugins/
│   └── requirement.md     ← plugin & dependency manifest
├── output/                ← generated artifacts (gitignored)
├── src/                   ← application source
└── docs/                  ← project documentation
```
