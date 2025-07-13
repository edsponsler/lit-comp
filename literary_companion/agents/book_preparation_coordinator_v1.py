# literary_companion/agents/book_preparation_coordinator_v1.py

from google.adk.agents import Agent
from literary_companion.config import DEFAULT_AGENT_MODEL

# We ONLY need to import the single tool the agent uses.
# The old imports for gcs_tool and translation_tool are no longer needed here.
from literary_companion.tools.gcs_tool import book_processor_tool

PREPARATION_AGENT_INSTRUCTION = """
Your goal is to prepare a classic novel for the Literary Companion.
You will be given the GCS bucket and file name.
You MUST call the `process_and_translate_book` tool with the provided `bucket_name` and `file_name` to perform the entire workflow.
Your final response MUST be the result message returned by the tool.
"""

book_preparation_coordinator = Agent(
    name="BookPreparationCoordinator_v1",
    model=DEFAULT_AGENT_MODEL,
    description="Orchestrates the one-time processing of a novel by calling a single master tool.",
    tools=[book_processor_tool],
)