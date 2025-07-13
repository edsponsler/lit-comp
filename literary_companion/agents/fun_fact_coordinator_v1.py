# literary_companion/agents/fun_fact_coordinator_v1.py

from google.adk.agents import Agent
from literary_companion.config import DEFAULT_AGENT_MODEL

# We import the single, powerful tool this agent is allowed to use.
from literary_companion.tools.fun_fact_orchestrator import fun_fact_orchestrator_tool

# This instruction is deliberately simple and direct.
FUN_FACT_AGENT_INSTRUCTION = """
You are a helpful coordinator. Your ONLY task is to generate fun facts for a user based on the text they have read.

You MUST call the `run_fun_fact_generation` tool to do this.

The user will provide you with the following arguments in their request:
- `text_segment`: The portion of the novel the user has read so far.
- `session_id`: The user's reading session ID.
- `agency_task_id`: A unique ID for this specific fun fact request.

You MUST pass these arguments directly to the `run_fun_fact_generation` tool.
Your final response MUST be the JSON object returned by the tool.
"""

fun_fact_coordinator = Agent(
    name="FunFactCoordinator_v1",
    model=DEFAULT_AGENT_MODEL,
    description="Manages the real-time generation of fun facts by invoking a deterministic orchestrator.",
    instruction=FUN_FACT_AGENT_INSTRUCTION,
    # This agent is highly specialized and only has one tool.
    tools=[fun_fact_orchestrator_tool],
)