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


async def main(book_name: str, chapter_number: int):
    """Runs the refactored, more efficient ADK-based fun fact generation workflow."""
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
    # The agent now handles its own data loading and caching.
    coordinator = FunFactCoordinatorAgent(
        fun_fact_types=fun_fact_types,
        book_name=book_name,
        chapter_number=chapter_number
    )

    # 3. Initialize the runner
    runner = Runner(agent=coordinator, app_name=app_name, session_service=session_service)

    # 4. Create a session with an empty initial state.
    # The agent is now self-contained and will fetch its own data.
    session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id, state={}
    )

    # 5. Run the agent and wait for it to complete
    print(f"--- Running Fun Fact Generation for session: {session_id} ---")
    # The content of the message does not matter, it just triggers the agent.
    content = types.Content(role="user", parts=[types.Part(text="Go.")])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # Let the loop run to completion to ensure all agents have finished.
        pass

    # 6. Retrieve and print the final result
    final_session = session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    final_result = final_session.state.get("final_fun_facts", {})

    print("\n--- Final Fun Facts ---")
    if final_result:
        print(json.dumps(final_result, indent=4))
    else:
        print("No fun facts were generated. Check logs for errors.")
    print("-----------------------\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Fun Fact Generation ADK agent.")
    parser.add_argument("--book", required=True, help="The name of the book (e.g., 'frankenstein' or 'frankenstein.txt').")
    parser.add_argument("--chapter", type=int, required=True, help="The chapter number to generate fun facts for.")
    args = parser.parse_args()

    # Ensure the GCS_BUCKET_NAME is set, as the agent now relies on it directly.
    if not os.environ.get("GCS_BUCKET_NAME"):
        print("Error: The GCS_BUCKET_NAME environment variable must be set.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(main(args.book, args.chapter))
