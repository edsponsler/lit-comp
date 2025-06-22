# file: cie_core/agents/coordinator_agent.py

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from cie_core.config import DEFAULT_AGENT_MODEL

# Import other agents and the micro task board tools
from cie_core.agents.information_retrieval_specialist import information_retrieval_specialist
from cie_core.agents.report_formatting_specialist import report_formatting_specialist
from cie_core.agents.data_analysis_specialist import data_analysis_specialist 
from decon.data_analysis.tools.micro_task_board_tool import post_micro_entry, get_micro_entries

# --- Tool Definitions ---
# Wrap the specialist agents in AgentTool wrappers
information_retrieval_adapter_tool = AgentTool(agent=information_retrieval_specialist)
report_formatting_adapter_tool = AgentTool(agent=report_formatting_specialist)
data_analysis_adapter_tool = AgentTool(agent=data_analysis_specialist) 

# Create tools that directly wrap the task board functions
status_board_writer_tool = FunctionTool(post_micro_entry)
status_board_reader_tool = FunctionTool(get_micro_entries)

print("Agent Tools for Coordinator have been instantiated.")

# --- The Final Coordinator Agent Definition ---
coordinator_agent = Agent(
    name="CoordinatorAgent_v1",
    model=DEFAULT_AGENT_MODEL,
    description="Orchestrates report generation by coordinating specialists.",
    instruction=(
        "You are a master Coordinator Agent. Your job is to manage a three-phase process to generate a report.\n"
        "You will be given a user query and a session_id. You must use the provided session_id for all operations and pass it to any specialist you call.\n\n"
        "**Overall Plan:**\n"
        "1.  **Phase 1: Information Retrieval**\n"
        "    a.  Call the `InformationRetrievalSpecialist_v1` tool to gather raw information.\n"
        "    b.  After the specialist is done, call the `get_micro_entries` tool to fetch the list of search result dictionaries it posted to the board.\n\n"
        "2.  **Phase 2: Data Analysis**\n"
        "    a.  Process the list of search results: iterate through each dictionary, extract the value of the 'content' key, and join them into a single, large string.\n"
        "    b.  Call the `DataAnalysisSpecialist_v1` tool, passing it the single, combined string of text to be analyzed.\n"
        "    c.  After the specialist is done, call `get_micro_entries` again to fetch the analysis results (a dictionary with 'narrative_summary' and 'key_points').\n\n"
        "3.  **Phase 3: Report Formatting**\n"
        "    a.  Take the analysis dictionary from Phase 2 and pass it to the `ReportFormattingSpecialist_v1` tool. Instruct it to write a comprehensive, multi-paragraph narrative report.\n"
        "    b.  After the specialist is done, call `get_micro_entries` one last time to fetch the final, formatted report.\n\n"
        "4.  **Final Delivery**\n"
        "    a.  Extract the final report text from the 'report' key of the payload retrieved in the previous step.\n"
        "    b.  **Your final answer MUST be ONLY the report text and nothing else.** Do not add any conversational text. Return only the report text."
    ),
    tools=[
        information_retrieval_adapter_tool,
        data_analysis_adapter_tool,
        report_formatting_adapter_tool,
        status_board_writer_tool,
        status_board_reader_tool
    ]
)

print(f"Agent '{coordinator_agent.name}' created with correctly aligned tools.")