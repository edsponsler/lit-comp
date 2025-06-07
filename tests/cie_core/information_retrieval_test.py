# tests/cie_core/information_retrieval_test.py
# Use: python -m tests.cie_core.information_retrieval_test
import asyncio
import uuid
import os
import importlib

# Ensure the ADK and Google libraries are importable
from google.adk.runners import Runner 
from google.adk.sessions import InMemorySessionService 
from google.genai import types as genai_types 

# Import your agent
from cie_core.agents.information_retrieval_specialist import information_retrieval_specialist

from cie_core.tools import status_board_tool

# Reload the status board tool to ensure we have the latest version; don't do this in production code
def get_latest_status_board_tool():
    importlib.reload(status_board_tool)
    from cie_core.tools.status_board_tool import get_status as get_status_from_board
    return get_status_from_board

# Load environment variables from .env file, especially if GOOGLE_APPLICATION_CREDENTIALS is there
# or to ensure GOOGLE_CLOUD_PROJECT is loaded for the db client implicitly.
from dotenv import load_dotenv
load_dotenv()

async def test_retrieval_agent():
    # Setup session and runner
    session_service_retrieval = InMemorySessionService() 
    app_name_retrieval = "cie_retrieval_test_app" 
    user_id_retrieval = "test_user_retrieval" 

    # Generate unique session_id and task_id for this test run
    current_session_id = f"session_{str(uuid.uuid4())}" 
    current_task_id = f"task_{str(uuid.uuid4())}" 

    session_service_retrieval.create_session( 
        app_name=app_name_retrieval,
        user_id=user_id_retrieval,
        session_id=current_session_id
    )
    print(f"Test session created: {current_session_id}") 

    runner_retrieval = Runner( 
        agent=information_retrieval_specialist,
        app_name=app_name_retrieval,
        session_service=session_service_retrieval
    )
    print(f"Runner created for agent '{runner_retrieval.agent.name}'.") 

    # Simulate a task from the Coordinator, including session_id and task_id in the query
    # as per the agent's instructions.
    user_query = ( 
        f"Please find information on 'Hubble Space Telescope'. " 
        f"Use session_id: {current_session_id} and task_id: {current_task_id} for status updates." 
    )
    print(f"\n>>> Sending task to InformationRetrievalSpecialist: {user_query}") 

    # Create the message content
    content = genai_types.Content(role='user', parts=[genai_types.Part(text=user_query)]) 
    
    final_response_text = "Agent did not produce a final response."
    print("\n--- Iterating through agent events ---")
    event_count = 0
    async for event in runner_retrieval.run_async(
        user_id=user_id_retrieval,
        session_id=current_session_id,
        new_message=content
    ):
        event_count += 1
        print(f"\n--- Event {event_count} ---")
        print(f"Type: {type(event)}")
        if hasattr(event, 'app_name'): print(f"App Name: {event.app_name}")
        if hasattr(event, 'user_id'): print(f"User ID: {event.user_id}")
        if hasattr(event, 'session_id'): print(f"Session ID: {event.session_id}")
        if hasattr(event, 'turn_id'): print(f"Turn ID: {event.turn_id}")
        if hasattr(event, 'agent_id'): print(f"Agent ID: {event.agent_id}")
        
        if event.content and event.content.parts:
            print(f"Content Parts ({len(event.content.parts)}):")
            for i, part in enumerate(event.content.parts):
                print(f"  Part {i+1}:")
                if hasattr(part, 'text') and part.text:
                    print(f"    Text: \"{part.text.strip()}\"")
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    print(f"    Function Call: {fc.name}")
                    # Be careful logging fc.args if they are very large
                    args_str = str(fc.args)
                    if len(args_str) > 300: # Truncate large args for printing
                        args_str = args_str[:300] + "... (truncated)"
                    print(f"    Args: {args_str}")
                if hasattr(part, 'function_result') and part.function_result:
                    fr = part.function_result
                    print(f"    Function Result: {fr.name}")
                    # Be careful logging fr.response if it's very large
                    response_str = str(fr.response)
                    if len(response_str) > 300: # Truncate large response for printing
                        response_str = response_str[:300] + "... (truncated)"
                    print(f"    Response: {response_str}")

        if event.is_final_response():
            print(">>> This event IS the final response from the agent. <<<")
            if event.content and event.content.parts and event.content.parts[0].text:
                final_response_text = event.content.parts[0].text
            break 
        else:
            print("--- This event is NOT the final response. ---")

    print(f"\nLoop finished. Total events processed: {event_count}")
    
    print(f"<<< InformationRetrievalSpecialist Response: {final_response_text}") 

    # Check Firestore for status updates using the reader tool
    print("\n--- Checking Status Board for updates (directly from script) ---") 
    
    try:
        get_status_from_board = get_latest_status_board_tool()
        # Call the imported get_status function directly
        status_check_task = get_status_from_board(session_id=current_session_id, task_id=current_task_id) 
        print(f"Status Board for task {current_task_id}: {status_check_task}")  

        status_check_all_session = get_status_from_board(session_id=current_session_id) 
        print(f"All Statuses for session {current_session_id}: {status_check_all_session}")  
    except Exception as e:
        print(f"Error calling imported get_status_from_board: {e}")

if __name__ == "__main__":
    # Ensure GOOGLE_CLOUD_PROJECT is set if not already in the environment for db client
    # For example, by loading .env or ensuring it's set in your shell
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("Warning: GOOGLE_CLOUD_PROJECT environment variable not set. Firestore client might fail.")

    asyncio.run(test_retrieval_agent()) 