# cie_core/agents/information_retrieval_specialist.py

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from cie_core.config import DEFAULT_AGENT_MODEL
from decon.data_analysis.tools.micro_task_board_tool import post_micro_entry
from cie_core.tools.search_tools import simple_web_search_tool

status_board_updater_tool = FunctionTool(post_micro_entry)

information_retrieval_specialist = Agent(
    name="InformationRetrievalSpecialist_v1",
    model=DEFAULT_AGENT_MODEL,
    description="A specialist agent that retrieves information from the web and posts the findings to a shared task board.",
    instruction=(
        "You are an Information Retrieval Specialist. Your task is to find and gather information on a given topic.\n"
        "You will be given a `user_query`, a `session_id`, and a `task_id` for your specific retrieval job.\n"
        "Your steps are:\n"
        "1.  Acknowledge the task. Immediately use the `post_micro_entry` tool. For this first call, you MUST provide the `task_id` you were given as the `entry_id` argument, and set the `status` to 'processing_request'.\n"
        "2.  Use the `simple_web_search_tool` to find relevant information based on the `user_query`.\n"
        "3.  Once you have the search results, you MUST use the `post_micro_entry` tool a second time to post your findings. For this second call:\n"
        "    -   You MUST use the exact same `task_id` from the initial request in the `entry_id` argument to ensure you are updating the correct task.\n"
        "    -   Set the `status` to 'completed_task'.\n"
        "    -   Place the entire list of search result dictionaries directly into the `output_payload_dict` argument.\n"
        "4.  Your final response to the coordinator MUST be a simple confirmation message, like 'Information retrieved and posted to the board.'"
    ),
    tools=[
        status_board_updater_tool,
        simple_web_search_tool
    ],
)

print(f"Agent '{information_retrieval_specialist.name}' created with corrected tools.")