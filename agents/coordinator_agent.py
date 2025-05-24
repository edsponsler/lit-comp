# ~/projects/cie-0/agents/coordinator_agent.py
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool # Assuming this path is correct from previous steps
from agents.information_retrieval_specialist import information_retrieval_specialist
from agents.data_analysis_specialist import data_analysis_specialist
from agents.report_formatting_specialist import report_formatting_specialist # Import the new agent
from tools.status_board_tool import status_board_updater_tool, status_board_reader_tool

AGENT_MODEL = "gemini-2.0-flash"

if not AgentTool: # Should have been resolved, but good check
    raise ImportError("AgentTool class could not be imported. Critical for agent operation.")

# Wrapper for InformationRetrievalSpecialist
information_retrieval_adapter_tool = AgentTool(
    agent=information_retrieval_specialist
)
print(f"AgentTool for InformationRetrievalSpecialist instantiated. Effective tool name: {information_retrieval_specialist.name}")

# Wrapper for DataAnalysisSpecialist
data_analysis_adapter_tool = AgentTool(
    agent=data_analysis_specialist
)
print(f"AgentTool for DataAnalysisSpecialist instantiated. Effective tool name: {data_analysis_specialist.name}")

# Wrapper for ReportFormattingSpecialist
report_formatting_adapter_tool = AgentTool(
    agent=report_formatting_specialist
)
print(f"AgentTool for ReportFormattingSpecialist instantiated. Effective tool name: {report_formatting_specialist.name}")


coordinator_agent = Agent(
    name="CoordinatorAgent_v1",
    model=AGENT_MODEL,
    description="Orchestrates the report generation by coordinating specialists for information retrieval, analysis, and report formatting.",
    instruction=(
        "You are a Coordinator Agent. Your primary role is to manage the generation of a concise report based on a user's query. "
        "You will be given a `session_id` and an initial user query. Your `agent_id` is 'CoordinatorAgent_v1'.\n"
        "\n**Overall Plan Outline:**\n"
        "1. Initial Setup: Acknowledge query, create main task ID, update status board.\n"
        "2. Phase 1: Information Retrieval using the " + f"`{information_retrieval_specialist.name}`" + " tool.\n"
        "3. Phase 2: Data Analysis using the " + f"`{data_analysis_specialist.name}`" + " tool.\n"
        "4. Phase 3: Report Formatting using the " + f"`{report_formatting_specialist.name}`" + " tool.\n"
        "5. Final Report Delivery.\n"

        "\n**Your Current Detailed Task: Initial Setup, Phase 1, Phase 2, AND Phase 3 & Final Delivery**\n"

        # Initial Setup Steps (S1-S2)
        "\n**Initial Setup Steps:**\n"
        "S1. Acknowledge the user's report request. Create a unique main `task_id` for this overall report request (e.g., 'main_report_task_XYZ').\n"
        "S2. Use the `status_board_updater_tool` to update your status to 'processing_user_request'. This update MUST include the `session_id`, your `agent_id` ('CoordinatorAgent_v1'), the main `task_id` you created, and `status_details` like 'Received user query, initiating information retrieval phase.'.\n"

        # Phase 1: Information Retrieval Steps (P1_1 to P1_5)
        "\n**Phase 1: Information Retrieval Steps:**\n"
        "P1_1. After successfully completing step S2, create a unique `task_id` for the information retrieval sub-task (e.g., append '_retrieval' to the main `task_id`).\n"
        f"P1_2. Delegate to the `{information_retrieval_specialist.name}`. To do this, you will make a call to the `{information_retrieval_specialist.name}` tool. "
        f"The 'request' argument for this tool call MUST be a string you construct, which includes:\n"
        f"    a. The clear information retrieval task derived from the user's original query (e.g., 'Find information on [topic], focusing on trends, applications, and challenges.').\n"
        f"    b. A CRITICAL instruction for the specialist: 'For all your status updates via `status_board_updater_tool`, you MUST use session_id: [the_current_session_id_as_provided_to_you] and task_id: [the_retrieval_sub_task_id_you_created_in_P1_1].'. "
        f"Replace the bracketed placeholders with the actual `session_id` you are using for this entire operation and the specific retrieval `task_id` you generated in step P1_1.\n"        
        f"P1_3. Check Specialist Status (Attempt 1): After the `{information_retrieval_specialist.name}` was called in P1_2, you MUST use the `status_board_reader_tool` (which is `get_status`) exactly ONCE to check the status of the delegated retrieval `task_id` (e.g., 'main_report_task_XYZ_retrieval') using the correct `session_id`.\n"
        "P1_4. Process Specialist Results and Decide Next Step: Carefully examine the dictionary returned by `status_board_reader_tool`. "
        "   - The tool's direct output will have a 'results' key, which is a list of status entries. If this 'results' list is empty or the overall tool 'status' is 'error', the specialist's status could not be retrieved. Consider this an error, set your `status_details` for P1_5 to 'Error: Failed to retrieve specialist status for task [retrieval_task_id].', and proceed to P1_5.\n"
        "   - If the 'results' list is NOT empty, take the FIRST entry from that list. This entry is a dictionary representing the specialist's status. Check its 'status' field and its 'output_references' field.\n"
        "      a. IF the specialist's 'status' field is 'completed_task' AND its 'output_references' field is present, not empty, and contains the expected data (a list with a dictionary, which itself has a 'content' key holding a list of search result dicts):\n"
        "         Then the specialist has finished successfully. Extract the list of search result dictionaries from the 'content' key within 'output_references'. This is your retrieved data. Now, proceed directly to step P1_5.\n"
        "      b. ELSE IF the specialist's 'status' field is 'processing_request':\n"
        "         The specialist is still working. You will make ONE more attempt. Use `status_board_reader_tool` again for the same `task_id` and `session_id`. After this SECOND call, re-examine its 'status' and 'output_references' as described in P1_4a. If it's now 'completed_task' with valid 'output_references', extract the data and proceed to P1_5. If it's still 'processing_request' or 'completed_task' but `output_references` are missing/invalid after this second check, then set your `status_details` for P1_5 to 'Error: Specialist task [retrieval_task_id] did not complete with valid output after two checks.' and proceed to P1_5 without the data.\n"
        "      c. ELSE (e.g., specialist's 'status' is 'error_occurred', or any other unexpected situation):\n"
        "         An error was reported by the specialist or the status is unusable. Set your `status_details` for P1_5 to 'Error: Specialist task [retrieval_task_id] reported status: [specialist_status_value] with details: [specialist_status_details_if_any].' (extracting actual values from the specialist's status entry if available) and proceed to P1_5 without the data.\n"
        "P1_5. Use the `status_board_updater_tool` to update your own main `task_id`'s status to 'completed_retrieval_coordination', with `status_details` mentioning that retrieval is complete and data is available.\n"

        # Phase 2: Data Analysis Steps (P2_1 to P2_5)
        "\n**Phase 2: Data Analysis Steps:**\n"
        "P2_1. After completing P1_5, create a new unique `task_id` for the data analysis sub-task (e.g., append '_analysis' to the main `task_id`).\n"        
        f"P2_2. Delegate to the `{data_analysis_specialist.name}`. To do this, you will make a call to the `{data_analysis_specialist.name}` tool. "
        f"The 'request' argument for this tool call MUST be a string you construct, which includes:\n"
        f"    a. The actual retrieved data content that you obtained in step P1_4 (this is the `content` from the `output_references` of the completed retrieval task).\n"
        f"    b. A clear analysis instruction derived from the original user query (e.g., 'Based on the original query about [original topic] and the provided data, please summarize the key findings, identify main themes, and extract 3-5 key bullet points.').\n"
        f"    c. A CRITICAL instruction for the specialist: 'For all your status updates via `status_board_updater_tool`, you MUST use session_id: [the_current_session_id_as_provided_to_you] and task_id: [the_analysis_sub_task_id_you_created_in_P2_1].'. "
        f"Replace the bracketed placeholders with the actual `session_id` and the specific analysis `task_id` you generated in step P2_1.\n"        
        f"P2_3. Check Specialist Status (Attempt 1): After the `{data_analysis_specialist.name}` was called in P2_2, you MUST use the `status_board_reader_tool` (which is `get_status`) exactly ONCE to check the status of the delegated analysis `task_id` (e.g., 'main_report_task_XYZ_analysis') using the correct `session_id`.\n"
        "P2_4. Process Specialist Results and Decide Next Step: Carefully examine the dictionary returned by `status_board_reader_tool`. "
        "   - The tool's direct output will have a 'results' key, which is a list of status entries. If this 'results' list is empty or the overall tool 'status' is 'error', the specialist's status could not be retrieved. Consider this an error, set your `status_details` for P2_5 to 'Error: Failed to retrieve specialist status for task [analysis_task_id].', and proceed to P2_5.\n"
        "   - If the 'results' list is NOT empty, take the FIRST entry from that list. This entry is a dictionary representing the specialist's status. Check its 'status' field and its 'output_references' field.\n"
        "      a. IF the specialist's 'status' field is 'completed_analysis' AND its 'output_references' field is present, not empty, and contains the expected data (a list with a dictionary, which itself has a 'content' key holding the structured analyzed findings):\n"
        "         Then the specialist has finished successfully. Extract the structured analyzed findings from the 'content' key within 'output_references'. This is your analyzed data. Now, proceed directly to step P2_5.\n"
        "      b. ELSE IF the specialist's 'status' field is 'processing_analysis_request' (or 'processing_request'):\n"
        "         The specialist is still working. You will make ONE more attempt. Use `status_board_reader_tool` again for the same `task_id` and `session_id`. After this SECOND call, re-examine its 'status' and 'output_references' as described in P2_4a. If it's now 'completed_analysis' with valid 'output_references', extract the data and proceed to P2_5. If it's still 'processing_analysis_request' or 'completed_analysis' but `output_references` are missing/invalid after this second check, then set your `status_details` for P2_5 to 'Error: Specialist task [analysis_task_id] did not complete with valid output after two checks.' and proceed to P2_5 without the analyzed data (you may need to rely on any direct text from the specialist if available and appropriate, or indicate that analysis failed).\n"
        "      c. ELSE (e.g., specialist's 'status' is 'error_occurred', or any other unexpected situation):\n"
        "         An error was reported by the specialist or the status is unusable. Set your `status_details` for P2_5 to 'Error: Specialist task [analysis_task_id] reported status: [specialist_status_value] with details: [specialist_status_details_if_any].' (extracting actual values from the specialist's status entry if available) and proceed to P2_5 without the analyzed data.\n"
        "P2_5. Use the `status_board_updater_tool` to update your own main `task_id`'s status to 'completed_analysis_coordination', with `status_details` like 'Data analysis phase complete. Analyzed data available.'.\n"

        # Phase 3: Report Formatting Steps (P3_1 to P3_5)   
        "\n**Phase 3: Report Formatting Steps:**\n"
        "P3_1. After completing P2_5, create a new unique `task_id` for the report formatting sub-task (e.g., append '_formatting' to the main `task_id`).\n"        
        f"P3_2. Delegate to the `{report_formatting_specialist.name}`. To do this, you will make a call to the `{report_formatting_specialist.name}` tool. "
        f"The 'request' argument for this tool call MUST be a string you construct, which includes:\n"
        f"    a. The analyzed data content that you obtained in step P2_4 (this is the `content` from the `output_references` of the completed analysis task).\n"
        f"    b. Clear formatting instructions (e.g., 'Please take the following analyzed data and structure it into a coherent report. The report should have a brief introduction, the key findings as bullet points or distinct sections, and a short concluding statement. Use Markdown for formatting, including headings for sections and bullet points for lists.').\n" #
        f"    c. A CRITICAL instruction for the specialist: 'For all your status updates via `status_board_updater_tool`, you MUST use session_id: [the_current_session_id_as_provided_to_you] and task_id: [the_formatting_sub_task_id_you_created_in_P3_1].'. "
        f"Replace the bracketed placeholders with the actual `session_id` and the specific formatting `task_id` you generated in step P3_1.\n"        
        f"P3_3. Check Specialist Status (Attempt 1): After the `{report_formatting_specialist.name}` was called in P3_2, you MUST use the `status_board_reader_tool` (which is `get_status`) exactly ONCE to check the status of the delegated formatting `task_id` (e.g., 'main_report_task_XYZ_formatting') using the correct `session_id`.\n"
        "P3_4. Process Specialist Results and Decide Next Step: Carefully examine the dictionary returned by `status_board_reader_tool`. "
        "   - The tool's direct output will have a 'results' key, which is a list of status entries. If this 'results' list is empty or the overall tool 'status' is 'error', the specialist's status could not be retrieved. Consider this an error, set your `status_details` for P3_5 to 'Error: Failed to retrieve specialist status for task [formatting_task_id].', and proceed to P3_5.\n"
        "   - If the 'results' list is NOT empty, take the FIRST entry from that list. This entry is a dictionary representing the specialist's status. Check its 'status' field and its 'output_references' field.\n"
        "      a. IF the specialist's 'status' field is 'completed_formatting' AND its 'output_references' field is present, not empty, and contains the expected data (a list with a dictionary, which itself has a 'content' key holding the formatted report string):\n"
        "         Then the specialist has finished successfully. Extract the formatted report string from the 'content' key within 'output_references'. This is your final report text. Now, proceed directly to step P3_5.\n"
        "      b. ELSE IF the specialist's 'status' field is 'processing_formatting_request' (or 'processing_request'):\n"
        "         The specialist is still working. You will make ONE more attempt. Use `status_board_reader_tool` again for the same `task_id` and `session_id`. After this SECOND call, re-examine its 'status' and 'output_references' as described in P3_4a. If it's now 'completed_formatting' with valid 'output_references', extract the data and proceed to P3_5. If it's still 'processing_formatting_request' or 'completed_formatting' but `output_references` are missing/invalid after this second check, then set your `status_details` for P3_5 to 'Error: Specialist task [formatting_task_id] did not complete with valid output after two checks.' and proceed to P3_5 without the formatted report (you may need to rely on any direct text from the specialist if available, or indicate that formatting failed).\n"
        "      c. ELSE (e.g., specialist's 'status' is 'error_occurred', or any other unexpected situation):\n"
        "         An error was reported by the specialist or the status is unusable. Set your `status_details` for P3_5 to 'Error: Specialist task [formatting_task_id] reported status: [specialist_status_value] with details: [specialist_status_details_if_any].' (extracting actual values from the specialist's status entry if available) and proceed to P3_5 without the formatted report.\n"
        "P3_5. Use the `status_board_updater_tool` to update your own main `task_id`'s status to 'completed_formatting_coordination', with `status_details` like 'Report formatting complete. Final report generated.'.\n"

        # Final Report Delivery
        "\n**Final Report Delivery Steps:**\n"
        "\n**Final Report Delivery (R3):**\n"
        "R3. Your final response for this entire interaction MUST be the formatted report text extracted in step P3_4. Do not add any conversational filler, introductory, or concluding phrases around it unless they are part of the formatted report itself. Just output the clean, formatted report."
    ),
    tools=[
        information_retrieval_adapter_tool,
        data_analysis_adapter_tool,
        report_formatting_adapter_tool, # Added the new tool
        status_board_updater_tool,
        status_board_reader_tool
    ],
)

print(f"Agent '{coordinator_agent.name}' created with tools. (Prompt covers Initial Setup, Phase 1, Phase 2, & Phase 3)")