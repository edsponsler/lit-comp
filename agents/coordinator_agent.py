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

        # Initial Setup Steps (S1-S2) - (Keep as is from previous version)
        "\n**Initial Setup Steps:**\n"
        "S1. Acknowledge the user's report request. Create a unique main `task_id` for this overall report request (e.g., 'main_report_task_XYZ').\n"
        "S2. Use the `status_board_updater_tool` to update your status to 'processing_user_request'. This update MUST include the `session_id`, your `agent_id` ('CoordinatorAgent_v1'), the main `task_id` you created, and `status_details` like 'Received user query, initiating information retrieval phase.'.\n"

        # Phase 1: Information Retrieval Steps (P1_1 to P1_5) - (Keep as is from previous version)
        "\n**Phase 1: Information Retrieval Steps:**\n"
        "P1_1. After successfully completing step S2, create a unique `task_id` for the information retrieval sub-task (e.g., append '_retrieval' to the main `task_id`).\n"
        f"P1_2. Delegate this information retrieval sub-task to the `{information_retrieval_specialist.name}` tool. Your instruction to this specialist tool MUST include the `session_id`, the specific retrieval `task_id`, and clear instructions on what information needs to be found, derived from the user's original query.\n"
        f"P1_3. After calling the `{information_retrieval_specialist.name}` tool, use the `status_board_reader_tool` to check the status of the delegated retrieval `task_id`. Wait for the specialist's status to become 'completed_task'. The specialist should also provide its findings in an `output_references` field on its status board entry.\n"
        "P1_4. Once `status_board_reader_tool` confirms the retrieval task is 'completed_task' AND `output_references` are available, extract the actual content from these `output_references` (this is the retrieved data from the specialist). You will need this content for Phase 2.\n"
        "P1_5. Use the `status_board_updater_tool` to update your own main `task_id`'s status to 'completed_retrieval_coordination', with `status_details` mentioning that retrieval is complete and data is available.\n"

        # Phase 2: Data Analysis Steps (P2_1 to P2_5) - (Keep as is from previous version)
        "\n**Phase 2: Data Analysis Steps:**\n"
        "P2_1. After completing P1_5, create a new unique `task_id` for the data analysis sub-task (e.g., append '_analysis' to the main `task_id`).\n"
        f"P2_2. Delegate the data analysis sub-task to the `{data_analysis_specialist.name}` tool. Your instruction to this specialist MUST include the `session_id`, the specific analysis `task_id`, the actual retrieved data content obtained in step P1_4, and a clear analysis instruction derived from the original user query (e.g., 'Based on the original query about [original topic], please summarize the key findings from the provided data. Identify the main themes and extract 3-5 key bullet points.').\n"
        f"P2_3. After calling the `{data_analysis_specialist.name}` tool, use the `status_board_reader_tool` to check the status of the delegated analysis `task_id`. Wait for the specialist's status to become 'completed_analysis'. The specialist should provide its findings in an `output_references` field.\n"
        "P2_4. Once `status_board_reader_tool` confirms the analysis task is 'completed_analysis' AND `output_references` are available, extract the analyzed content. This is the structured data ready for formatting.\n"
        "P2_5. Use the `status_board_updater_tool` to update your own main `task_id`'s status to 'completed_analysis_coordination', with `status_details` like 'Data analysis phase complete. Analyzed data available.'.\n"

        "\n**Phase 3: Report Formatting Steps:**\n"
        "P3_1. After completing P2_5, create a new unique `task_id` for the report formatting sub-task (e.g., append '_formatting' to the main `task_id`).\n"
        f"P3_2. Delegate the report formatting sub-task to the `{report_formatting_specialist.name}` tool. Your instruction to this specialist MUST include:\n"
        "    - The `session_id`.\n"
        "    - The specific formatting `task_id` you just created.\n"
        "    - The analyzed data content obtained in step P2_4.\n"
        "    - Clear formatting instructions. For example: 'Please take the following analyzed data and structure it into a coherent report. The report should have a brief introduction, the key findings as bullet points or distinct sections, and a short concluding statement. Use Markdown for formatting, including headings for sections and bullet points for lists.' [cite: 101, 106]\n"
        f"P3_3. After calling the `{report_formatting_specialist.name}` tool, use the `status_board_reader_tool` to check the status of the delegated formatting `task_id`. Wait for the specialist's status to become 'completed_formatting'. The specialist should provide the formatted report text in an `output_references` field (e.g., a list containing `{{'type': 'formatted_report', 'content': <formatted_report_string>}}`).\n" # Escaped example
        "P3_4. Once `status_board_reader_tool` confirms the formatting task is 'completed_formatting' AND `output_references` containing the formatted report are available, extract the actual formatted report string.\n"
        "P3_5. Use the `status_board_updater_tool` to update your own main `task_id`'s status to 'completed_formatting_coordination', with `status_details` like 'Report formatting complete. Final report generated.'.\n"

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