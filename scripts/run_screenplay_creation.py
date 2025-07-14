# In scripts/run_screenplay_creation.py

import asyncio
import os
import uuid
import argparse
import sys
from google.adk.runners import Runner
from literary_companion.agents.screenplay_coordinator_v1 import screenplay_coordinator
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

async def main(bucket: str, file: str, action: str, chapters: str | None):
    """
    Initializes and runs the ScreenplayCoordinator_v1 agent.
    """
    # The screenplay tool expects the '_prepared.json' file which contains the modern translation.
    # We will derive this from the input .txt file name.
    if not file.endswith('.txt'):
        print(f"Error: Input file '{file}' must be a .txt file.", file=sys.stderr)
        return

    prepared_file_name = file.replace('.txt', '_prepared.json')
    print(f"Using prepared file for screenplay generation: gs://{bucket}/{prepared_file_name}")

    app_name = "literary-companion-screenwriter"
    session_service = InMemorySessionService()

    runner = Runner(
        agent=screenplay_coordinator,
        app_name=app_name,
        session_service=session_service,
    )
    
    # The prompt will provide the necessary arguments for the tool.
    if action == "beatsheet":
        prompt = f"Please create a beat sheet for the novel located in the bucket '{bucket}' with the filename '{prepared_file_name}'."
    elif action == "scenelist":
        if not chapters:
            print("ERROR: --chapters is required when using the 'scenelist' action.", file=sys.stderr)
            return
        prompt = (
            f"Please generate a scene list for '{chapters}' from the novel "
            f"located in the bucket '{bucket}' with the filename '{prepared_file_name}'."
        )
    else:
        print(f"ERROR: Unknown action '{action}'. This should not happen.", file=sys.stderr)
        return

    user_id = "user_cli_tool"
    session_id = f"session_{uuid.uuid4()}"
    session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    initial_message = Content(role="user", parts=[Part(text=prompt)])

    final_response = "No final response received from agent."
    # The runner will call the agent, which will use the beat_sheet_tool with the arguments from the prompt.
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=initial_message
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
    print("--- Agent Final Response ---")
    print(final_response)

if __name__ == "__main__":
    # The script now uses environment variables set by gcenv.sh
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    file_name = os.environ.get("GCS_FILE_NAME")

    if not all([bucket_name, file_name]):
        print("ERROR: GCS_BUCKET_NAME and GCS_FILE_NAME environment variables must be set.", file=sys.stderr)
        print("Please run 'source gcenv.sh <IDENTIFIER>' before running this script.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Run the screenplay creation agent.")
    parser.add_argument(
        "--action",
        required=True,
        choices=["beatsheet", "scenelist"],
        help="The action to perform: 'beatsheet' for a high-level outline, or 'scenelist' for a detailed scene breakdown."
    )
    parser.add_argument(
        "--chapters",
        help="The range of chapters to process for the 'scenelist' action (e.g., 'Chapters 1 through 16')."
    )
    args = parser.parse_args()

    asyncio.run(main(bucket=bucket_name, file=file_name, action=args.action, chapters=args.chapters))