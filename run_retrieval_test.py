# ~/projects/cie-0/run_retrieval_test.py
import asyncio
import uuid
import os

# Ensure the ADK and Google libraries are importable
from google.adk.runners import Runner # [cite: 269]
from google.adk.sessions import InMemorySessionService # [cite: 269]
from google.genai import types as genai_types # [cite: 269]

# Import your agent
from agents.information_retrieval_specialist import information_retrieval_specialist

# Import the get_status function directly, not just the tool wrapper
from tools.status_board_tool import get_status as get_status_from_board # Renamed to avoid confusion

# Import the status board reader tool if you want to try querying Firestore from the script
# (though the agent itself only uses the updater tool)
from tools.status_board_tool import status_board_reader_tool # [cite: 269]

# Load environment variables from .env file, especially if GOOGLE_APPLICATION_CREDENTIALS is there
# or to ensure GOOGLE_CLOUD_PROJECT is loaded for the db client implicitly.
from dotenv import load_dotenv
load_dotenv()

async def test_retrieval_agent():
    # Setup session and runner
    session_service_retrieval = InMemorySessionService() # [cite: 269]
    app_name_retrieval = "cie_retrieval_test_app" # [cite: 269]
    user_id_retrieval = "test_user_retrieval" # [cite: 269]

    # Generate unique session_id and task_id for this test run
    current_session_id = f"session_{str(uuid.uuid4())}" # [cite: 269]
    current_task_id = f"task_{str(uuid.uuid4())}" # [cite: 269]

    session_service_retrieval.create_session( # [cite: 269]
        app_name=app_name_retrieval,
        user_id=user_id_retrieval,
        session_id=current_session_id
    )
    print(f"Test session created: {current_session_id}") # [cite: 270]

    runner_retrieval = Runner( # [cite: 270]
        agent=information_retrieval_specialist,
        app_name=app_name_retrieval,
        session_service=session_service_retrieval
    )
    print(f"Runner created for agent '{runner_retrieval.agent.name}'.") # [cite: 270]

    # Simulate a task from the Coordinator, including session_id and task_id in the query
    # as per the agent's instructions.
    user_query = ( # [cite: 270]
        f"Please find information on 'the future of renewable energy'. " # [cite: 271]
        f"Use session_id: {current_session_id} and task_id: {current_task_id} for status updates." # [cite: 271]
    )
    print(f"\n>>> Sending task to InformationRetrievalSpecialist: {user_query}") # [cite: 271]

    # Create the message content
    content = genai_types.Content(role='user', parts=[genai_types.Part(text=user_query)]) # [cite: 271]

    final_response_text = "Agent did not produce a final response." # [cite: 271]
    async for event in runner_retrieval.run_async( # [cite: 271]
        user_id=user_id_retrieval, 
        session_id=current_session_id, 
        new_message=content
    ):
        if event.is_final_response(): # [cite: 272]
            if event.content and event.content.parts: # [cite: 272]
                final_response_text = event.content.parts[0].text # [cite: 272]
            break

    print(f"<<< InformationRetrievalSpecialist Response: {final_response_text}") # [cite: 272]

    # Check Firestore for status updates using the reader tool
    print("\n--- Checking Status Board for updates (directly from script) ---") # [cite: 272]

    try:
        # Call the imported get_status function directly
        status_check_task = get_status_from_board(session_id=current_session_id, task_id=current_task_id) 
        print(f"Status Board for task {current_task_id}: {status_check_task}") # 

        status_check_all_session = get_status_from_board(session_id=current_session_id) 
        print(f"All Statuses for session {current_session_id}: {status_check_all_session}") # 
    except Exception as e:
        print(f"Error calling imported get_status_from_board: {e}")

if __name__ == "__main__":
    # Ensure GOOGLE_CLOUD_PROJECT is set if not already in the environment for db client
    # For example, by loading .env or ensuring it's set in your shell
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("Warning: GOOGLE_CLOUD_PROJECT environment variable not set. Firestore client might fail.")

    asyncio.run(test_retrieval_agent()) # [cite: 273]