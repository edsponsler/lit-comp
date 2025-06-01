# ~/projects/cie-0/run_cie_coordinator_test.py
import asyncio
import uuid
import os
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from agents.coordinator_agent import coordinator_agent
from tools.status_board_tool import get_status as get_status_from_board
from dotenv import load_dotenv

load_dotenv()

async def cie_coordinator_test():
    session_service_coordinator = InMemorySessionService()
    app_name_coordinator = "cie_coordinator_test_app"
    user_id_coordinator = "cie_coordinator_test_user"
    current_session_id = f"session_{str(uuid.uuid4())}"
    
    session_service_coordinator.create_session(
        app_name=app_name_coordinator,
        user_id=user_id_coordinator,
        session_id=current_session_id
    )
    print(f"Test session created for Coordinator Agent: {current_session_id}")

    runner_coordinator = Runner(
        agent=coordinator_agent,
        app_name=app_name_coordinator,
        session_service=session_service_coordinator
    )
    print(f"Runner created for agent '{runner_coordinator.agent.name}'.")

    user_query_text = (
        f"User Query: Generate a report on 'Emergent Intelligence research inspired by Marvin Minsky's theory 'Society of Mind'. "
        f"Please use session_id: {current_session_id} for all your operations."
    )
    
    print(f"\n>>> Sending task to Coordinator Agent: {user_query_text}")
    
    initial_content = genai_types.Content(role='user', parts=[genai_types.Part(text=user_query_text)])
    
    final_response_text = "Coordinator Agent did not produce a final response."
    
    print("\n--- Iterating through agent events ---")
    
    i = 0
    async for event in runner_coordinator.run_async(
        user_id=user_id_coordinator,
        session_id=current_session_id,
        new_message=initial_content
    ):
        print(f"Event {i}: Type: {type(event)}")
        
        # Check for function calls in the event content parts
        if event.content and event.content.parts:
            for part_index, part in enumerate(event.content.parts):
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    print(f"  Event {i}, Part {part_index}: Function Call: {fc.name}({fc.args})")
                elif hasattr(part, 'text') and part.text:
                    print(f"  Event {i}, Part {part_index}: Text: \"{part.text.strip()}\"")

        # Use the is_final_response() method
        if event.is_final_response():
            print(f"  Event {i}: Detected as final response.")
            if event.content and event.content.parts:
                # Concatenate text from all parts for the final response
                final_response_text = "".join(part.text for part in event.content.parts if part.text)
            else:
                final_response_text = "Final event had no text content."
            break  # Exit loop once final response is processed
        
        i += 1

    print(f"\n<<< Coordinator Agent Final Response: {final_response_text}")

    print("\n--- Checking Agent Status Board for updates (directly from script) ---")
    try:
        status_check_all_session = get_status_from_board(session_id=current_session_id)
        print(f"All Statuses for session {current_session_id}:")
        if status_check_all_session.get("results"):
            for entry in status_check_all_session["results"]:
                # Ensuring all relevant fields are printed
                details = entry.get('status_details', 'N/A')
                output_refs = entry.get('output_references', 'N/A')
                print(f"  - Agent: {entry.get('agent_id')}, Task: {entry.get('task_id')}, Status: {entry.get('status')}, Details: {details}, Output: {output_refs}")
        else:
            print(f"  No status entries found for session {current_session_id} or error: {status_check_all_session.get('message')}")

    except Exception as e:
        print(f"Error calling imported get_status_from_board: {e}")

if __name__ == "__main__":
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("Warning: GOOGLE_CLOUD_PROJECT environment variable not set. Firestore client might fail.")
    asyncio.run(cie_coordinator_test())
