# ~/projects/cie-0/agents/information_retrieval_specialist.py
from google.adk.agents import Agent

# Correctly import the tools from your project structure
# Assuming your project root 'cie-0' is in the Python path or you run from there.
# If you run from ~/projects/cie-0, these imports should work.
from tools.status_board_tool import status_board_updater_tool
from tools.search_tools import search_tool

AGENT_MODEL = "gemini-2.0-flash" # Or your preferred model [cite: 263]

information_retrieval_specialist = Agent(
    name="InformationRetrievalSpecialist_v1", # [cite: 263]
    model=AGENT_MODEL, # [cite: 264]
    description=( # [cite: 264]
        "Specializes in finding and retrieving textual information from the web " # [cite: 264]
        "based on a given topic or query. It updates a central status board " # [cite: 265]
        "with its progress and results." # [cite: 265]
    ),
    instruction=( # [cite: 265]
        "You are an Information Retrieval Specialist. Your task is to find relevant " # [cite: 265]
        "information on a given topic. " # [cite: 265]
        "1. Receive a task description, a `session_id`, and a `task_id` from the Coordinator. " # [cite: 265]
        "2. Update your status on the Agent Status Board using `status_board_updater_tool` " # [cite: 265]
        "to 'processing_request' with the provided `session_id` and `task_id`. " # [cite: 265]
        "3. Formulate an effective search query based on the task description. " # [cite: 266]
        "4. Use the `search_tool` to find relevant information (URLs and snippets). " # [cite: 266]
        "5. If the search is successful, store the retrieved URLs and snippets. " # [cite: 266]
        "For this version, you can consider the snippets as the primary content. " # [cite: 266]
        "6. Update your status on the Agent Status Board using `status_board_updater_tool` " # [cite: 266]
        "to 'completed_task'. Include the `session_id`, `task_id`, and set " # [cite: 266]
        "`output_references` to a list containing a dictionary like: " # [cite: 267]
        "`{'type': 'retrieved_data', 'content': <list_of_results_dicts>}`. " # [cite: 267]
        "If an error occurred, update status to 'error_occurred' with " # [cite: 267]
        "`status_details` explaining the error. " # [cite: 267]
        "7. Your final response should be a confirmation message to the coordinator " # [cite: 268]
        "including the task_id and a summary of what you did or if an error occurred." # [cite: 268]
    ),
    tools=[search_tool, status_board_updater_tool], # [cite: 268]
)

print(f"Agent '{information_retrieval_specialist.name}' created.") # [cite: 268]