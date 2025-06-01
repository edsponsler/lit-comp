import asyncio
import uuid
import os
from flask import Flask, render_template, request, jsonify
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from agents.coordinator_agent import coordinator_agent 
from dotenv import load_dotenv

load_dotenv() 

app = Flask(__name__)

# Ensure GOOGLE_CLOUD_PROJECT is set for ADK and Firestore client initialization
# The ADK might try to initialize clients (like for Vertex AI) when agents are imported
# or when the Runner is created. Firestore client is used by status_board_tool.
if not os.getenv("GOOGLE_CLOUD_PROJECT"): 
    print("CRITICAL: GOOGLE_CLOUD_PROJECT environment variable not set.") 
    # Consider raising an error or exiting if this is critical for startup

# Initialize session service for the Coordinator Agent (can be a global instance for the app)
# Note: InMemorySessionService is per-instance. If Cloud Run scales to multiple instances,
# session state via this service won't be shared. However, CIE uses Firestore for true state
# via the status_board_tool, so this is mainly for ADK's session management within a single run.
session_service_coordinator = InMemorySessionService() 
app_name_coordinator = "cie_web_app" 
user_id_coordinator_prefix = "web_user_" 

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/process', methods=['POST'])
async def process_query(): # Flask 2.0+ supports async routes
    try:
        data = request.get_json() 
        user_query_topic = data.get('query') 
        if not user_query_topic: 
            return jsonify({"message": "Query cannot be empty."}), 400 

        current_session_id = f"session_{str(uuid.uuid4())}" 
        # Use a unique user_id per request or a consistent one if you have user sessions
        current_user_id = f"{user_id_coordinator_prefix}{str(uuid.uuid4())}" 

        session_service_coordinator.create_session( 
            app_name=app_name_coordinator, 
            user_id=current_user_id, 
            session_id=current_session_id 
        )

        runner_coordinator = Runner( 
            agent=coordinator_agent, 
            app_name=app_name_coordinator, 
            session_service=session_service_coordinator 
        )

        # Construct the query for the Coordinator Agent, including session_id
        # Follow the pattern used in the tutorial's test script run_cie_coordinator_test.py
        coordinator_query_text = ( 
            f"User Query: Generate a report on '{user_query_topic}'.\n" 
            f"Please use session_id: {current_session_id} for all your operations." 
        )

        initial_content = genai_types.Content(role='user', parts=[genai_types.Part(text=coordinator_query_text)]) 
        final_report_text = f"Coordinator Agent did not produce a final report for session {current_session_id}." 

        async for event in runner_coordinator.run_async( 
            user_id=current_user_id, 
            session_id=current_session_id, 
            new_message=initial_content 
        ):
            if event.is_final_response(): 
                if event.content and event.content.parts and event.content.parts[0].text: 
                    final_report_text = event.content.parts[0].text 
                else:
                    final_report_text = f"Final response received for session {current_session_id}, but it contained no text." 
                break

        return jsonify({"report": final_report_text}) 

    except Exception as e: 
        print(f"Error processing request: {e}") 
        # Consider more specific error logging or user messages
        return jsonify({"message": f"An internal error occurred: {str(e)}"}), 500 

if __name__ == '__main__':
    # For local development. For production, use a WSGI server like Gunicorn.
    app.run(debug=True, port=5001) 
