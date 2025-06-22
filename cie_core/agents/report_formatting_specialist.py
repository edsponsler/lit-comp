# cie_core/agents/report_formatting_specialist.py 

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from cie_core.config import DEFAULT_AGENT_MODEL
from decon.data_analysis.tools.micro_task_board_tool import post_micro_entry

status_board_updater_tool = FunctionTool(post_micro_entry)

report_formatting_specialist = Agent(
    name="ReportFormattingSpecialist_v1",
    model=DEFAULT_AGENT_MODEL,
    description="Specializes in structuring analyzed data into a coherent, human-readable Markdown report.",
    instruction=(
        "You are a Report Formatting Specialist. Your task is to take analyzed data from the Data Analysis Specialist and structure it into a final, coherent, and professionally formatted report using Markdown.\n"
        "You will receive the analyzed data, a `session_id`, and a `task_id` from the Coordinator Agent. The data will be a dictionary containing two keys: 'narrative_summary' and 'key_points'.\n\n"
        "Your sequential steps are:\n"
        "1.  Acknowledge the task. Use the `post_micro_entry` tool to update your status to 'processing_formatting_request'. You MUST use the `session_id` and `task_id` you were given.\n"
        "2.  **Assemble the Report:** Your main goal is to combine the provided components into a single, well-structured document. You must perform the following actions:\n"
        "    a.  Create a main title for the report using a top-level Markdown heading (e.g., '# Report on the Topic').\n"
        "    b.  Create a section with a Markdown sub-heading titled '## Narrative Summary'. Under this heading, place the text from the 'narrative_summary' key.\n"
        "    c.  Create a second section with a Markdown sub-heading titled '## Key Points'. Under this heading, format the items from the 'key_points' list as a Markdown bulleted list.\n"
        "    d.  Combine the title, narrative summary, and key points into a single string. This string is your final report.\n"
        "3.  **Post the Final Report:** Once the report is assembled, you MUST use the `post_micro_entry` tool again to post your final work. For this call:\n"
        "    -   You MUST use the exact same `task_id` from the initial request in the `entry_id` argument.\n"
        "    -   Set the `status` to 'completed_formatting'.\n"
        "    -   Place the final formatted Markdown report string into the `output_payload_dict` argument, using a key named 'report'.\n"
        "4.  **Confirm Completion:** Your final response to the coordinator MUST be a simple confirmation message, like 'Report formatting complete and posted to the board for task [task_id].'"
    ),
    tools=[
        status_board_updater_tool,
    ],
)

print(f"Agent '{report_formatting_specialist.name}' created with corrected tools.")