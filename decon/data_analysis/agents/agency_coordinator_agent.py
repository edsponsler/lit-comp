from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# Import the Default Agent Model from CIE Core Config
from cie_core.config import DEFAULT_AGENT_MODEL

# Import our new micro-agent functions and micro-task board tools
from decon.data_analysis.tools.micro_task_board_tool import post_micro_entry, get_micro_entries
from decon.data_analysis.agents.data_analysis_micro_agents import extract_keywords, segment_sentences

# --- 1. Define the Instruction Prompt ---

# Ultra simple instruction for degugging purposes.
AGENCY_COORDINATOR_INSTRUCTION = """
You are a simple tool-using agent.
Your only job is to call the `segment_sentences_tool` with the provided text.
The tool will return a dictionary.
Your final response MUST be ONLY that dictionary.
"""

# --- 2. Wrap Functions into ADK FunctionTools ---
# This makes our Python functions callable by the LLM agent.
post_micro_entry_tool = FunctionTool(post_micro_entry)
get_micro_entries_tool = FunctionTool(get_micro_entries)
extract_keywords_tool = FunctionTool(extract_keywords)
segment_sentences_tool = FunctionTool(segment_sentences)


# --- 3. Define the Agent ---
agency_coordinator = Agent(
    name="DataAnalysisAgencyCoordinator_v1",
    model=DEFAULT_AGENT_MODEL,
    description="Orchestrates data analysis by coordinating micro-agents via a Micro-Task Board.",
    instruction=AGENCY_COORDINATOR_INSTRUCTION,
    tools=[
        post_micro_entry_tool,
        get_micro_entries_tool,
        extract_keywords_tool,
        segment_sentences_tool
    ]
)