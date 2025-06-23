# scripts/run_book_preparation.py

import sys
import os
import asyncio
import argparse
import uuid

# --- THE FIX: Initialize Vertex AI at the very top ---
# This must run before any other project modules are imported.
import vertexai
try:
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
    REGION = "us-central1"
    vertexai.init(project=PROJECT_ID, location=REGION)
    print(f"--- Vertex AI Initialized for Project: {PROJECT_ID} ---")
except Exception as e:
    print(f"--- CRITICAL: Failed to initialize Vertex AI in run_book_preparation.py. {e} ---")
    sys.exit(1) # Exit if initialization fails
# --------------------------------------------------

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from literary_companion.agents.book_preparation_coordinator_v1 import book_preparation_coordinator

async def main(bucket_name: str, file_name: str):
    """
    Runs the BookPreparationCoordinator_v1 agent to process a novel.
    """
    print(f"--- Starting preparation for gs://{bucket_name}/{file_name} ---")

    app_name = "literary-companion-preparer"
    session_service = InMemorySessionService()

    runner = Runner(
        agent=book_preparation_coordinator,
        app_name=app_name,
        session_service=session_service
    )

    user_id = "user_cli_tool"
    session_id = f"session_{uuid.uuid4()}"

    session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )

    initial_message_text = (
        f"Please prepare the novel located in the bucket '{bucket_name}' "
        f"with the filename '{file_name}'."
    )
    initial_message = Content(role="user", parts=[Part(text=initial_message_text)])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=initial_message
    ):
        is_tool_call_event = (
            event.content
            and event.content.parts
            and event.content.parts[0].function_call
        )

        if event.is_final_response():
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text
                print("\n--- Agent Final Response ---")
                print(final_text)
                print("--------------------------\n")
        elif is_tool_call_event:
             print(f"--- Calling Tool: {event.content.parts[0].function_call.name} ---")

    print("--- Preparation script finished. ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Literary Companion Book Preparation Agent.")
    parser.add_argument("--bucket", required=True, help="The GCS bucket name.")
    parser.add_argument("--file", required=True, help="The GCS file name of the novel's text.")
    args = parser.parse_args()

    # Ensure the required environment variable is set.
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        print("ERROR: The GOOGLE_CLOUD_PROJECT environment variable must be set.")
        sys.exit(1)

    asyncio.run(main(args.bucket, args.file))