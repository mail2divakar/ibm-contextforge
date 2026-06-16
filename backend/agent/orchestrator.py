"""
Agent Orchestrator — Epic 4 stub.

Epic 4 will implement a Vertex AI Gemini-based agent using function calling.

Vertex AI SDK pattern (Epic 4 implementation):
    import vertexai
    from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration

    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=VERTEX_AI_LOCATION)

    model = GenerativeModel(
        model_name="gemini-2.0-flash",
        tools=[sql_tool, graph_tool, semantic_tool],
        system_instruction=SYSTEM_PROMPT,
    )

    response = model.generate_content(user_message)

Tool routing rules (baked into system prompt):
  - Counting / distribution queries   → sql_analytics
  - Relationship / multi-hop queries  → graph_traversal
  - "Do we have X?" / similarity      → semantic_search
  - Compound queries                  → multiple tool calls in sequence

PII fence (system prompt constraint):
  "When building tool call arguments, NEVER include owner names, engineer names,
   or URLs in query text or filter values. These fields are retrieved after query
   and displayed to the user — they must not be sent as search parameters."
"""

import logging

logger = logging.getLogger(__name__)


def run_agent(query_text: str, conversation_id: str, history: list[dict]) -> dict:
    """Epic 4 stub. Returns a placeholder response."""
    logger.info("run_agent: Epic 4 stub — query='%s'", query_text)
    return {
        "answer": "Agent not yet implemented (Epic 4).",
        "results": [],
        "citation": "Epic 4 stub",
        "tool_used": None,
        "processing_ms": 0,
    }
