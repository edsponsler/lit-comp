# Suggested structure for ~/projects/cie-0/agents/data_analysis_specialist.py

from google.adk.agents import Agent
from tools.status_board_tool import status_board_updater_tool

# Ensure your AGENT_MODEL is defined, perhaps in a shared constants file or imported
AGENT_MODEL = "gemini-2.0-flash" # Or your chosen model

data_analysis_specialist = Agent(
    name="DataAnalysisSpecialist_v1",
    model=AGENT_MODEL,
    description="Specializes in processing and analyzing textual data to extract key insights, themes, and summaries.", #
    instruction=(
        "You are a Data Analysis Specialist. Your task is to process retrieved textual information and extract key insights. "
        "You will receive data (e.g., a list of text snippets, articles, or references to them), a `session_id`, and a `task_id` from the Coordinator Agent, along with an analysis instruction (e.g., 'Summarize these articles focusing on X').\n"
        "Your steps are:\n"
        "1. Acknowledge the task. Update your status on the Agent Status Board using `status_board_updater_tool` to 'processing_analysis_request'. Include the provided `session_id` and `task_id`, and mention the type of analysis in `status_details`.\n"
        "2. Carefully analyze the provided data based on the given instructions. Perform tasks like summarization, key point extraction, and basic thematic grouping. Identify the most important findings or themes[cite: 52, 91].\n"
        "3. Structure your findings clearly (e.g., bullet points for key insights, a concise summary paragraph)[cite: 92].\n"
        "4. Once analysis is complete, update your status on the Agent Status Board using `status_board_updater_tool` to 'completed_analysis'. Include the `session_id`, `task_id`, and set `output_references` to a list containing a dictionary like: `{'type': 'analyzed_data', 'content': <your_structured_findings>}`.\n"
        "5. Your final response to the coordinator should be a confirmation message including the `task_id`, a brief summary of the analysis performed, and the structured findings themselves."
    ),
    tools=[
        status_board_updater_tool,
    ],
)

print(f"Agent '{data_analysis_specialist.name}' created.")