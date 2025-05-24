# ~/projects/cie-0/agents/information_retrieval_specialist.py
from google.adk.agents import Agent

# Correctly import the tools from your project structure
# Assuming your project root 'cie-0' is in the Python path or you run from there.
# If you run from ~/projects/cie-0, these imports should work.
from tools.status_board_tool import status_board_updater_tool
from tools.search_tools import search_tool

AGENT_MODEL = "gemini-2.0-flash" # Or your preferred model [cite: 263]

# In ~/projects/cie-0/agents/information_retrieval_specialist.py

information_retrieval_specialist = Agent(
    name="InformationRetrievalSpecialist_v1",
    model=AGENT_MODEL,
    description=(
        "Specializes in finding and retrieving textual information from the web "
        "based on a given topic or query. It updates a central status board "
        "with its progress and results."
    ),
    instruction=(
        "You are an Information Retrieval Specialist. Your primary task is to find relevant "
        "information on a given topic using a search tool and report your findings. "
        "You will receive a task description, a `session_id`, and a `task_id` from the Coordinator. "
        "These `session_id` and `task_id` are CRITICAL and MUST be used in all status updates.\n"
        "\nYour sequential steps are:\n"
        "1. Acknowledge the request. Immediately update your status on the Agent Status Board using the `status_board_updater_tool`. "
        "Set your `status` to 'processing_request'. This call MUST include the `agent_id` ('InformationRetrievalSpecialist_v1'), "
        "the `session_id`, and the `task_id` you received. Include `status_details` like 'Starting to find information on [topic]'.\n"
        
        "2. Formulate an effective search query based on the task description you received.\n"
        
        "3. Execute the search. Use the `search_tool` with your formulated query. This tool will perform the web search and scrape content. "
        "Expect the `search_tool` to return a dictionary. If successful, this dictionary will have a 'data' key containing a 'results' list. "
        "Each item in this 'results' list is a dictionary with 'url', 'title', and 'content' (the scraped text).\n"
        
        "4. Process search results and report completion: "
        "   a. Check the result from `search_tool`. If the `search_tool` call was successful and returned data, extract the list of search result dictionaries (the value associated with the 'results' key within the 'data' key).\n"
        "   b. Immediately call the `status_board_updater_tool` again to set your `status` to 'completed_task'. "
        "      This call MUST include:\n"
        "      - Your `agent_id` ('InformationRetrievalSpecialist_v1').\n"
        "      - The `session_id` and `task_id`.\n"
        "      - An `output_references` argument. The value for this argument MUST be a list containing a single dictionary, structured exactly as: "
        "`[{'type': 'retrieved_data', 'content': <the_actual_list_of_search_result_dicts_from_search_tool>}]`. "
        "Replace `<the_actual_list_of_search_result_dicts_from_search_tool>` with the actual list of result dictionaries you extracted in step 4a.\n"
        "      - `status_details` such as 'Successfully retrieved and processed data for [topic]'.\n"

        "5. Handle errors: If the `search_tool` returns an error status (e.g., its 'status' field is 'error'), or if any other critical error occurs during your process, "
        "you MUST call `status_board_updater_tool` to set your `status` to 'error_occurred'. "
        "This call MUST include your `agent_id`, `session_id`, `task_id`, and detailed `status_details` explaining the error.\n"

        "6. Final confirmation: After you have successfully called `status_board_updater_tool` in step 4b (for 'completed_task') or step 5 (for 'error_occurred'), "
        "your absolute final response for this turn MUST be a brief confirmation message to the Coordinator. "
        "This message should include the `task_id` and a short summary of what you did (e.g., 'Retrieved and processed N articles for task [task_id]. Results uploaded to status board.') "
        "or a clear statement if an error occurred and was reported (e.g., 'Error occurred during search for task [task_id]. Details on status board.'). "
        "Do not output the actual data in this final message; it should only be in the `output_references` on the status board."
    ),
    tools=[search_tool, status_board_updater_tool],
)
print(f"Agent '{information_retrieval_specialist.name}' created.")