# scripts/run_fun_fact_creation_adk.py

import asyncio
import json
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from literary_companion.agents.fun_fact_adk_agents import FunFactCoordinatorAgent
from google.genai import types


async def main():
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
    coordinator = FunFactCoordinatorAgent(fun_fact_types=fun_fact_types)

    # 3. Initialize the runner
    runner = Runner(agent=coordinator, app_name=app_name, session_service=session_service)

    # 4. Create a session with the initial state
    # In a real application, this text would come from the user's reading session.
    text_segment = """
    It was a dark and stormy night; the rain fell in torrents — except at occasional intervals, 
    when it was checked by a violent gust of wind which swept up the streets (for it is in London 
    that our scene lies), rattling along the housetops, and fiercely agitating the scanty flame of 
    the lamps that struggled against the darkness.
    """
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
    print(final_result)
    print("-----------------------\n")


if __name__ == "__main__":
    asyncio.run(main())
