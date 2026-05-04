# CRM Digital — AI-Powered Customer Success

A customer relationship management platform with an AI-powered support agent ("Alex") that handles routine queries across email, WhatsApp, and web form 24/7.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the MCP server (agent tools)

```bash
# stdio mode — for use with Claude Desktop, Cursor, etc.
python -m src.mcp_server

# SSE mode — for remote access
python -m src.mcp_server --sse
```

### 4. Run tests

```bash
python -m pytest tests/ -v
```

## Architecture

```
Customer → [Email / WhatsApp / Web Form] → FastAPI webhook
                                                  │
                                            MCP Server
                                                  │
                                        Core Loop (process_ticket)
                                                  │
                                    ┌─────────────┼─────────────┐
                                    │             │             │
                              Language     Escalation    Category
                              Detect       Check         Classify
                                    │             │             │
                              Sentiment    KB Search    Plan Check
                              Analysis                  │
                                    │             │             │
                                    └─────────────┼─────────────┘
                                                  │
                                        Channel-Aware Reply
                                                  │
                                    ┌─────────────┼─────────────┐
                                    │             │             │
                              Log to DB     Record in     Send via
                              (tickets)     Memory        Channel
```

## Project Structure

```
crm-digital/
├── src/
│   ├── core_loop_prototype.py   # Core interaction loop (Exercise 1.2)
│   ├── conversation_state.py    # Memory and state tracking (Exercise 1.3)
│   ├── mcp_server.py            # MCP server with 8 tools (Exercise 1.4)
│   ├── agent/                   # Agent tool functions and Gemini schemas
│   ├── api/                     # FastAPI routes and daily reports
│   ├── channels/                # Gmail, WhatsApp, web form adapters
│   ├── db/                      # SQLAlchemy models and schema
│   ├── skills/                  # Agent skills manifest (8 skills)
│   ├── stitch/                  # NotebookLM enrichment pipeline
│   └── web/                     # React SupportForm component
├── tests/
│   ├── test_core_loop.py        # 45 tests for core loop
│   ├── test_conversation_state.py # 26 tests for memory/state
│   ├── test_mcp_server.py       # 24 tests for MCP tools
│   └── test_skills.py           # 36 tests for skill definitions
├── specs/
│   ├── discovery-log.md         # 10 hidden requirements from 55-ticket analysis
│   └── customer-success-fte-spec.md  # Full crystallization spec
├── context/                     # Product docs, brand voice, escalation rules
├── CLAUDE.md                    # Project instructions
└── requirements.txt             # Python dependencies
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_knowledge_base` | Search product docs for relevant info |
| `create_ticket` | Create + AI-process a support ticket |
| `get_customer_history` | Cross-channel interaction history |
| `escalate_to_human` | Route ticket to human agent queue |
| `send_response` | Deliver response via appropriate channel |
| `get_ticket_status` | Look up ticket details and state |
| `get_dashboard` | Global operations overview |
| `process_customer_message` | One-call end-to-end message processing |

## Performance

- **Testing:** 131/131 tests passing
- **Processing:** <0.01s per message (rules-based prototype)
- **Coverage:** Core loop, memory, MCP tools, skills, escalation, multilingual, plan awareness, channel formatting
