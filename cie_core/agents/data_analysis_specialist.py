# file: cie_core/agents/data_analysis_specialist.py

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from cie_core.config import DEFAULT_AGENT_MODEL
from decon.data_analysis.tools.micro_task_board_tool import post_micro_entry

status_board_updater_tool = FunctionTool(post_micro_entry)

data_analysis_specialist = Agent(
    name="DataAnalysisSpecialist_v1",
    model=DEFAULT_AGENT_MODEL,
    description="Specializes in processing and analyzing textual data to extract key insights, themes, and summaries.",
    instruction=(
        "You are a Data Analysis Specialist. Your task is to process retrieved textual information and extract key insights. "
        "You will receive a large body of text, a `session_id`, and a `task_id` from the Coordinator Agent.\n"
        "Your steps are:\n"
        "1.  Acknowledge the task. Use the `post_micro_entry` tool to update your status to 'processing_analysis_request'. You MUST use the `session_id` and `task_id` you were given.\n"
        "2.  Carefully analyze the provided text. Your goal is to identify the most important findings, themes, and key points. You must generate a comprehensive summary of the text.\n"
        "3.  Structure your findings as a dictionary containing two keys: 'narrative_summary' (a multi-paragraph summary of the content) and 'key_points' (a bulleted list of the most critical facts or themes).\n"
        "4.  Once analysis is complete, you MUST use the `post_micro_entry` tool again to post your findings. For this call:\n"
        "    -   You MUST use the exact same `task_id` in the `entry_id` argument.\n"
        "    -   Set the `status` to 'completed_analysis'.\n"
        "    -   Place the entire dictionary of your structured findings directly into the `output_payload_dict` argument.\n"
        "5.  Your final response to the coordinator MUST be a simple confirmation message, like 'Analysis complete and posted to the board for task [task_id].'"
    ),
    tools=[
        status_board_updater_tool,
    ],
)

print(f"Agent '{data_analysis_specialist.name}' created.")