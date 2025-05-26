import asyncio
import uuid
import os
from flask import Flask, render_template, request, jsonify
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from agents.coordinator_agent import coordinator_agent # [cite: 32]
from dotenv import load_dotenv

load_dotenv() # [cite: 32]

app = Flask(__name__)

# Ensure GOOGLE_CLOUD_PROJECT is set for ADK and Firestore client initialization
# The ADK might try to initialize clients (like for Vertex AI) when agents are imported
# or when the Runner is created. Firestore client is used by status_board_tool.
if not os.getenv("GOOGLE_CLOUD_PROJECT"): # [cite: 32, 33]
    print("CRITICAL: GOOGLE_CLOUD_PROJECT environment variable not set.") # [cite: 33]
    # Consider raising an error or exiting if this is critical for startup

# Initialize session service for the CoordinatorAgent (can be a global instance for the app)
# Note: InMemorySessionService is per-instance. If Cloud Run scales to multiple instances,
# session state via this service won't be shared. However, CIE uses Firestore for true state
# via the status_board_tool, so this is mainly for ADK's session management within a single run.
session_service_coordinator = InMemorySessionService() # [cite: 34]
app_name_coordinator = "cie_web_app" # [cite: 34]
user_id_coordinator_prefix = "web_user_" # [cite: 34]

@app.route('/')
def index():
    return render_template('index.html') # [cite: 35]

@app.route('/process', methods=['POST'])
async def process_query(): # Flask 2.0+ supports async routes
    try:
        data = request.get_json() # [cite: 35]
        user_query_topic = data.get('query') # [cite: 35]
        if not user_query_topic: # [cite: 35]
            return jsonify({"message": "Query cannot be empty."}), 400 # [cite: 36]

        current_session_id = f"session_{str(uuid.uuid4())}" # [cite: 36]
        # Use a unique user_id per request or a consistent one if you have user sessions
        current_user_id = f"{user_id_coordinator_prefix}{str(uuid.uuid4())}" # [cite: 36]

        session_service_coordinator.create_session( # [cite: 36]
            app_name=app_name_coordinator, # [cite: 36]
            user_id=current_user_id, # [cite: 36]
            session_id=current_session_id # [cite: 37]
        )

        runner_coordinator = Runner( # [cite: 37]
            agent=coordinator_agent, # [cite: 37]
            app_name=app_name_coordinator, # [cite: 37]
            session_service=session_service_coordinator # [cite: 37]
        )

        # Construct the query for the CoordinatorAgent, including session_id
        # This follows the pattern in the tutorial's test script [cite: 37, 38]
        coordinator_query_text = ( # [cite: 38]
            f"User Query: Generate a report on '{user_query_topic}'.\n" # [cite: 38]
            f"Please use session_id: {current_session_id} for all your operations." # [cite: 39]
        )

        initial_content = genai_types.Content(role='user', parts=[genai_types.Part(text=coordinator_query_text)]) # [cite: 39]
        final_report_text = f"CoordinatorAgent did not produce a final report for session {current_session_id}." # [cite: 39]

        async for event in runner_coordinator.run_async( # [cite: 39]
            user_id=current_user_id, # [cite: 40]
            session_id=current_session_id, # [cite: 40]
            new_message=initial_content # [cite: 40]
        ):
            if event.is_final_response(): # [cite: 40]
                if event.content and event.content.parts and event.content.parts[0].text: # [cite: 40]
                    final_report_text = event.content.parts[0].text # [cite: 41]
                else:
                    final_report_text = f"Final response received for session {current_session_id}, but it contained no text." # [cite: 41]
                break

        return jsonify({"report": final_report_text}) # [cite: 41]

    except Exception as e: # [cite: 42]
        print(f"Error processing request: {e}") # [cite: 42]
        # Consider more specific error logging or user messages
        return jsonify({"message": f"An internal error occurred: {str(e)}"}), 500 # [cite: 42]

if __name__ == '__main__':
    # For local development. For production, use a WSGI server like Gunicorn.
    app.run(debug=True, port=5001) # [cite: 43]