import asyncio
import uuid
import os
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from decon.data_analysis.agents.agency_coordinator_agent import agency_coordinator
from decon.data_analysis.tools.micro_task_board_tool import get_micro_entries

async def main():
    print("--- Testing Data Analysis Agency Coordinator ---")
    run_uuid = str(uuid.uuid4())
    session_id = f"session_test_coord_{run_uuid}"
    agency_task_id = f"agency_task_test_coord_{run_uuid}"

    sample_text = (
        "The Collaborative Insight Engine (CIE) is a multi-agent system. "
        "Its goal is to generate reports based on user queries. "
        "The system uses a coordinator and several specialist agents."
    )

    # ULTIMATE-SIMPLICITY PROMPT
    initial_prompt = (
        f"text_to_analyze: \"{sample_text}\""
    )

    session_service = InMemorySessionService()
    session_service.create_session(
        app_name="test_agency_coordinator", user_id="test_user", session_id=session_id)

    runner = Runner(
        agent=agency_coordinator, app_name="test_agency_coordinator", session_service=session_service)

    print("\n>>> Running the Agency Coordinator agent with FINAL simplified prompt...")
    final_report_str = ""
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session_id,
        new_message=Content(parts=[Part(text=initial_prompt)])
    ):
        # We don't need the verbose logging anymore
        if event.is_final_response() and event.content and event.content.parts:
            final_report_str = event.content.parts[0].text

    print("<<< Agent run finished.")
    print("\n--- Final Report from Agent (Should be a dictionary) ---")
    print(f"Raw report string: {final_report_str}")

    # FINAL VERIFICATION LOGIC
    try:
        # The agent's final output is a string representation of a dictionary.
        # We can't use json.loads because it uses single quotes.
        # A safe way to evaluate it is with ast.literal_eval.
        import ast
        final_report_dict = ast.literal_eval(final_report_str)
        if isinstance(final_report_dict, dict) and "sentences" in final_report_dict:
            num_sentences = len(final_report_dict["sentences"])
            print(f"[VERIFY] Success! Agent returned a dictionary with {num_sentences} sentences.")
            assert num_sentences == 3
        else:
            print("[VERIFY] FAILED: Agent did not return the expected dictionary.")
    except (ValueError, SyntaxError) as e:
        print(f"[VERIFY] FAILED: Could not parse the agent's final report. Error: {e}")

    print("\n--- Test Finished ---")

if __name__ == "__main__":
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        print("CRITICAL: GOOGLE_CLOUD_PROJECT environment variable not set.")
    else:
        asyncio.run(main())