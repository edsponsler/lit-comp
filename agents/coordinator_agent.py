# ~/projects/cie-0/agents/coordinator_agent.py
from google.adk.agents import Agent
from agents.information_retrieval_specialist import information_retrieval_specialist
from tools.status_board_tool import status_board_updater_tool, status_board_reader_tool

try:
    from google.adk.tools.agent_tool import AgentTool
    print("Successfully imported AgentTool from google.adk.tools.agent_tool")
except ImportError:
    try:
        from google.adk.tools import AgentTool
        print("Successfully imported AgentTool from google.adk.tools")
    except ImportError as e_tools_direct:
        print(f"Failed to import AgentTool from google.adk.tools: {e_tools_direct}")
        AgentTool = None

AGENT_MODEL = "gemini-2.0-flash"

if AgentTool:
    # MODIFIED HERE: Removed 'description' argument. Only 'agent' argument remains.
    information_retrieval_adapter_tool = AgentTool(
        agent=information_retrieval_specialist
    )
    effective_tool_name = information_retrieval_specialist.name
    print(f"AgentTool instantiated with only the agent. Effective tool name expected: {effective_tool_name}")
else:
    raise ImportError("AgentTool class could not be imported. Please check ADK version (0.5.0) documentation or library structure for the correct AgentTool import path.")

coordinator_agent = Agent(
    name="CoordinatorAgent_v1",
    model=AGENT_MODEL,
    description="Orchestrates the report generation process by coordinating specialist agents.",
    instruction=(
        "You are a Coordinator Agent. Your primary role is to manage the generation of a concise report based on a user's query. "
        "You will be given a `session_id` and an initial user query. You must also generate a main `task_id` for the overall report. \n"
        "Your current tasks are:\n"
        "1. Receive the user's report request. Create a main `task_id` for this request.\n"
        "2. Update your status on the Agent Status Board using `status_board_updater_tool` to 'processing_user_request', including the `session_id` and your main `task_id`.\n"
        "3. Decompose the request. The first step is always information retrieval. Create a unique `task_id` for this sub-task (e.g., by appending '_retrieval' to the main `task_id`).\n"
        f"4. Delegate this information retrieval sub-task to the `{information_retrieval_specialist.name}` tool. Your instruction to the specialist must include the `session_id` and the specific sub-task `task_id` you generated for retrieval. The instruction should clearly state what information needs to be found (based on the user's query).\n"
        "5. After delegating, use `status_board_reader_tool` to check the status of the delegated retrieval sub-task using its `session_id` and `task_id`.\n"
        f"6. Once the `{information_retrieval_specialist.name}` tool completes (as verified by the status board or its direct response), confirm its completion and briefly summarize the outcome or the data reference provided by the specialist. If it returns data directly, present that. \n"
        "7. Update your status on the Agent Status Board using `status_board_updater_tool` to 'completed_retrieval_coordination' (or 'error_in_retrieval_coordination' if issues arose).\n"
        "Your final response should be a message confirming the actions taken and the results from the Information Retrieval Specialist."
    ),
    tools=[
        information_retrieval_adapter_tool,
        status_board_updater_tool,
        status_board_reader_tool
    ],
)

print(f"Agent '{coordinator_agent.name}' created, attempting to use wrapped tool. Referenced in prompt as: '{information_retrieval_specialist.name}'.")