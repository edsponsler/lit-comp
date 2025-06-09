from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from cie_core.config import DEFAULT_AGENT_MODEL
from decon.data_analysis.orchestrator import run_data_analysis_agency

# Define the instruction for this simple specialist
DATA_ANALYSIS_V2_INSTRUCTION = """
You are a simple data analysis specialist agent.
When you receive a request, your ONLY job is to call the `run_data_analysis_agency_tool`.
After the tool runs, its dictionary result will be provided to you.
Your final response for the entire task MUST be ONLY that result dictionary from the tool.
Do not add any text, explanation, or conversational filler.
"""

# Create a single tool for the agent to use
run_data_analysis_agency_tool = FunctionTool(run_data_analysis_agency)

# Define the new specialist agent
data_analysis_specialist_v2 = Agent(
    name="DataAnalysisSpecialist_v2",
    model=DEFAULT_AGENT_MODEL,
    description="A specialist agent that uses a deterministic Python orchestrator to run the data analysis agency.",
    instruction=DATA_ANALYSIS_V2_INSTRUCTION,
    tools=[run_data_analysis_agency_tool]
)