"""
Gemini function-calling tool declarations.
These tell Gemini what tools exist, what parameters they take,
and when to use them.
"""

from google.genai import types

GEMINI_TOOLS = [
    types.Tool(
        function_declarations=[

            types.FunctionDeclaration(
                name="get_or_create_customer",
                description="Look up a customer by email. Creates a new record if not found.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "email":   types.Schema(type=types.Type.STRING, description="Customer email address"),
                        "name":    types.Schema(type=types.Type.STRING, description="Customer full name"),
                        "phone":   types.Schema(type=types.Type.STRING, description="Phone / WhatsApp number"),
                        "company": types.Schema(type=types.Type.STRING, description="Company name"),
                    },
                    required=["email"],
                ),
            ),

            types.FunctionDeclaration(
                name="create_ticket",
                description="Create a new support ticket and log the first customer message.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "customer_id": types.Schema(type=types.Type.STRING, description="UUID from get_or_create_customer"),
                        "channel":     types.Schema(type=types.Type.STRING, description="email | whatsapp | web_form"),
                        "subject":     types.Schema(type=types.Type.STRING, description="Short subject line"),
                        "body":        types.Schema(type=types.Type.STRING, description="Full customer message"),
                        "priority":    types.Schema(type=types.Type.STRING, description="low | medium | high | critical"),
                    },
                    required=["customer_id", "channel", "subject", "body"],
                ),
            ),

            types.FunctionDeclaration(
                name="update_ticket_status",
                description="Update a ticket status. Use resolved when done, escalated when routing to humans.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "ticket_id":    types.Schema(type=types.Type.STRING),
                        "status":       types.Schema(type=types.Type.STRING, description="open|in_progress|waiting_customer|escalated|resolved|closed"),
                        "escalated_to": types.Schema(type=types.Type.STRING, description="Human queue name if escalating"),
                    },
                    required=["ticket_id", "status"],
                ),
            ),

            types.FunctionDeclaration(
                name="set_ticket_sentiment",
                description="Score customer sentiment: -1.0 (very negative) to 1.0 (very positive).",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "ticket_id": types.Schema(type=types.Type.STRING),
                        "score":     types.Schema(type=types.Type.NUMBER, description="Float between -1.0 and 1.0"),
                    },
                    required=["ticket_id", "score"],
                ),
            ),

            types.FunctionDeclaration(
                name="get_customer_history",
                description="Fetch the customer's recent ticket history to personalise the response.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "customer_id": types.Schema(type=types.Type.STRING),
                        "limit":       types.Schema(type=types.Type.INTEGER, description="Max tickets to return (default 5)"),
                    },
                    required=["customer_id"],
                ),
            ),

            types.FunctionDeclaration(
                name="search_knowledge_base",
                description="Search past solutions before crafting a reply. Always call this first.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "category": types.Schema(type=types.Type.STRING, description="billing | login | feature | bug | other"),
                        "keyword":  types.Schema(type=types.Type.STRING, description="Key term from the customer message"),
                    },
                ),
            ),

            types.FunctionDeclaration(
                name="add_to_knowledge_base",
                description="After resolving a ticket, save the problem/solution so the agent learns.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "ticket_id": types.Schema(type=types.Type.STRING),
                        "category":  types.Schema(type=types.Type.STRING),
                        "problem":   types.Schema(type=types.Type.STRING),
                        "solution":  types.Schema(type=types.Type.STRING),
                    },
                    required=["ticket_id", "category", "problem", "solution"],
                ),
            ),

            types.FunctionDeclaration(
                name="log_agent_reply",
                description="Log the agent's outbound reply to the ticket message history.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "ticket_id": types.Schema(type=types.Type.STRING),
                        "body":      types.Schema(type=types.Type.STRING, description="The reply text sent to the customer"),
                    },
                    required=["ticket_id", "body"],
                ),
            ),

            types.FunctionDeclaration(
                name="escalate_ticket",
                description=(
                    "Escalate to a human agent. Call when: billing/legal/security issue, "
                    "customer is very angry, or agent cannot resolve in 2 attempts."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "ticket_id": types.Schema(type=types.Type.STRING),
                        "reason":    types.Schema(type=types.Type.STRING, description="Why escalating"),
                        "queue":     types.Schema(type=types.Type.STRING, description="Human queue name (default: tier-2-support)"),
                    },
                    required=["ticket_id", "reason"],
                ),
            ),
        ]
    )
]
