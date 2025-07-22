# scripts/run_fun_fact_creation_adk.py

import asyncio
import json
import uuid
import argparse
import os
import sys

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from literary_companion.agents.fun_fact_adk_agents import FunFactCoordinatorAgent
from google.genai import types
from literary_companion.tools.gcs_tool import read_gcs_object


async def main(book_name: str, chapter_number: int):
    """Runs the ADK-based fun fact generation workflow."""
    session_service = InMemorySessionService()
    app_name = "literary-companion-adk"
    user_id = "user-1234"
    session_id = str(uuid.uuid4())

    # 1. Define the fun fact types to generate
    fun_fact_types = [
        "historical_context",
        "geographical_setting",
        "plot_points",
        "character_sentiments",
        "character_relationships",
    ]

    # 2. Create the coordinator agent
    coordinator = FunFactCoordinatorAgent(
        fun_fact_types=fun_fact_types, 
        book_name=book_name, 
        chapter_number=chapter_number
    )

    # 3. Initialize the runner
    runner = Runner(agent=coordinator, app_name=app_name, session_service=session_service)

    # 4. Create a session with the initial state
    base_name, _ = os.path.splitext(book_name)
    prepared_book_path = f"{base_name}_prepared.json"
    try:
        bucket_name = os.environ.get("GCS_BUCKET_NAME")
        if not bucket_name:
            print("Error: GCS_BUCKET_NAME environment variable is not set.", file=sys.stderr)
            return

        book_data = json.loads(read_gcs_object(bucket_name, prepared_book_path))
        paragraphs = [p["original_text"] for p in book_data["paragraphs"] if p["chapter_number"] == chapter_number]
        text_segment = "\n".join(paragraphs)
    except Exception as e:
        print(f"Error reading or processing book file: {e}")
        return

    initial_state = {"text_segment": text_segment}
    session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id, state=initial_state
    )

    # 5. Run the agent and wait for it to complete
    print(f"--- Running Fun Fact Generation for session: {session_id} ---")
    content = types.Content(role="user", parts=[types.Part(text="Generate fun facts.")])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # Let the loop run to completion to ensure all agents have finished.
        pass

    # 6. Retrieve and print the final result
    final_session = session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    final_result = final_session.state.get("final_fun_facts", {})

    print("\n--- Final Fun Facts ---")
    print(json.dumps(final_result, indent=4))
    print("-----------------------\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Fun Fact Generation ADK agent.")
    parser.add_argument("--book", required=True, help="The name of the book (e.g., 'frankenstein' or 'frankenstein.txt').")
    parser.add_argument("--chapter", type=int, required=True, help="The chapter number to generate fun facts for.")
    args = parser.parse_args()
    asyncio.run(main(args.book, args.chapter))
