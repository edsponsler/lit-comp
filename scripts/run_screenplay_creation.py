# In scripts/run_screenplay_creation.py

import asyncio
import os
import uuid
import argparse
import json
import sys
import re
from google.adk.runners import Runner
from literary_companion.agents.screenplay_coordinator_v2 import screenplay_coordinator_v2
from literary_companion.tools.screenplay_v2_tool import get_novel_text_for_chapters
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from google.cloud import storage

def get_paragraphs_for_chapters(bucket_name: str, file_name: str, chapters_str: str) -> list[dict]:
    """
    Fetches and filters paragraphs from a prepared JSON file in GCS
    based on a chapter string (e.g., "Chapters 1 through 5").
    """
    match = re.match(r"Chapters (\d+) through (\d+)", chapters_str, re.IGNORECASE)
    if not match:
        return []
    start_chapter, end_chapter = int(match.group(1)), int(match.group(2))

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        file_contents = blob.download_as_string()
        data = json.loads(file_contents)
        
        return [
            p for p in data.get("paragraphs", [])
            if p.get("chapter_number") and start_chapter <= int(p["chapter_number"]) <= end_chapter
        ]
    except Exception as e:
        print(f"Error fetching or parsing prepared file from GCS: {e}", file=sys.stderr)
        return []

def save_screenplay_to_gcs(bucket_name: str, file_path: str, content: str):
    """Uploads a string content to a file in GCS."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        blob.upload_from_string(content, content_type='text/markdown')
        print(f"\nSuccessfully saved screenplay to gs://{bucket_name}/{file_path}")
    except Exception as e:
        print(f"\nError saving screenplay to GCS: {e}", file=sys.stderr)


async def main(bucket: str, file: str, chapters: str, use_mocks: bool):
    """
    Initializes and runs the ScreenplayCoordinatorV2 agent.
    """
    if not file.endswith('.txt'):
        print(f"Error: Input file '{file}' must be a .txt file.", file=sys.stderr)
        return

    initial_state = {}
    if not use_mocks:
        prepared_file_name = file.replace('.txt', '_prepared.json')
        print(f"Using prepared file for screenplay generation: gs://{bucket}/{prepared_file_name}")
        paragraphs = get_paragraphs_for_chapters(bucket, prepared_file_name, chapters)
        if not paragraphs:
            print(f"Error: Could not retrieve paragraphs for '{chapters}'. Aborting.", file=sys.stderr)
            return
        initial_state["paragraphs"] = paragraphs

    app_name = "literary-companion-screenwriter-v2"
    session_service = InMemorySessionService()

    runner = Runner(
        agent=screenplay_coordinator_v2,
        app_name=app_name,
        session_service=session_service,
    )

    user_id = "user_cli_tool"
    session_id = f"session_{uuid.uuid4()}"

    # Prepare initial state
    if use_mocks:
        initial_state["use_mocks"] = True
        print("--- RUNNING IN MOCK MODE ---")

    session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id, state=initial_state)

    initial_message = Content(role="user", parts=[Part(text=f"Generate a screenplay for the provided novel text, focusing on {chapters}.")])

    final_response = "No final response received from agent."
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=initial_message
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text

    final_session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    # Prioritize getting the result from the state, but fall back to the
    # agent's final text response if the state key isn't present.
    final_screenplay = final_session.state.get("final_screenplay")
    if not final_screenplay:
        final_screenplay = final_response

    # --- New logic to handle per-chapter screenplays ---
    chapter_screenplays = final_session.state.get("chapter_screenplays")

    if chapter_screenplays and isinstance(chapter_screenplays, dict):
        print(f"\n--- Generated {len(chapter_screenplays)} Chapter Screenplay(s) ---")
        folder_name = file.replace('.txt', '')
        
        for chapter_num, screenplay_text in sorted(chapter_screenplays.items()):
            print(f"\n--- Chapter {chapter_num} Screenplay ---")
            # Print a snippet of the screenplay for verification
            print(screenplay_text[:500] + "..." if len(screenplay_text) > 500 else screenplay_text)

            if not use_mocks:
                output_filename = f"chapter_{chapter_num}_screenplay.md"
                output_path = f"{folder_name}/{output_filename}"
                save_screenplay_to_gcs(bucket, output_path, screenplay_text)
    else:
        # Fallback for error or if no screenplays were generated
        print("--- No chapter-specific screenplays found in state. ---")
        print("--- Final Agent Response ---")
        print(final_response)


if __name__ == "__main__":
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    file_name = os.environ.get("GCS_FILE_NAME")

    if not all([bucket_name, file_name]):
        print("ERROR: GCS_BUCKET_NAME and GCS_FILE_NAME environment variables must be set.", file=sys.stderr)
        print("Please run 'source gcenv.sh <IDENTIFIER>' before running this script.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Run the enhanced screenplay creation agent.")
    parser.add_argument(
        "--chapters",
        required=True,
        help="The range of chapters to process (e.g., 'Chapters 1 through 16')."
    )
    parser.add_argument(
        "--use_mocks",
        action="store_true",
        help="Use mock data instead of calling LLMs to reduce cost."
    )
    args = parser.parse_args()

    asyncio.run(main(bucket=bucket_name, file=file_name, chapters=args.chapters, use_mocks=args.use_mocks))
