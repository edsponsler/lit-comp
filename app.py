import asyncio
import uuid
import json
import os
import vertexai
from flask import Flask, render_template, request, jsonify
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from cie_core.agents.coordinator_agent import coordinator_agent 
from google.genai.types import Content, Part 
from literary_companion.tools.gcs_tool import read_text_from_gcs
from literary_companion.agents.fun_fact_coordinator_v1 import fun_fact_coordinator
from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv

load_dotenv() 

app = Flask(__name__)

# The Vertex AI library is initialized automatically by the client libraries
# reading the GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION environment
# variables. These are set for the Cloud Run service in deploy_cloud_run.sh.
# No explicit vertexai.init() call is needed here.


# Initialize session service for the Coordinator Agent (can be a global instance for the app)
# Note: InMemorySessionService is per-instance. If Cloud Run scales to multiple instances,
# session state via this service won't be shared. However, CIE uses Firestore for true state
# via the status_board_tool, so this is mainly for ADK's session management within a single run.
session_service_coordinator = InMemorySessionService() 
app_name_coordinator = "cie_web_app" 
user_id_coordinator_prefix = "web_user_" 

@app.route('/')
def index():
    return render_template("cie_core/index.html") 

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

# Create a dedicated session service for the LITERARY COMPANION module
session_service_lc = InMemorySessionService()

# LITERARY COMPANION 1: Serve the Literary Companion HTML page
@app.route("/literary_companion")
def literary_companion_page():
    """Renders the main page for the Literary Companion module."""
    # We need to tell Flask to look for the template in our module's directory
    return render_template("literary_companion/literary_companion.html")

# LITERARY COMPANION 2: The API endpoint for generating fun facts
@app.route("/generate_fun_facts", methods=["POST"])
async def generate_fun_facts():
    """
    Receives user progress and runs the FunFactCoordinator_v1 agent.
    """
    req_data = request.get_json()
    text_segment = req_data.get("text_segment")
    session_id = req_data.get("session_id")

    if not all([text_segment, session_id]):
        return jsonify({"error": "Missing required fields: text_segment, session_id"}), 400

    print("--- API: Received request for fun facts. ---")
    runner_lc = Runner(
        agent=fun_fact_coordinator,
        app_name="literary-companion-fun-facts",
        session_service=session_service_lc,
    )
    user_id = f"user_{session_id}"
    agency_task_id = f"task_{uuid.uuid4()}"
    session_service_lc.create_session(
        app_name="literary-companion-fun-facts", user_id=user_id, session_id=agency_task_id
    )
    request_text = (
        f"Generate fun facts for session_id '{session_id}' and "
        f"agency_task_id '{agency_task_id}'. The text segment is: {text_segment}"
    )
    initial_message = Content(role="user", parts=[Part(text=request_text)])

    try:
        final_facts_json_string = None
        # We will loop through the events to find the one that contains our tool's direct response
        async for event in runner_lc.run_async(
            user_id=user_id, session_id=agency_task_id, new_message=initial_message
        ):
            # Check if the event part contains a function_response with the correct name
            if (event.content and 
                event.content.parts and
                event.content.parts[0].function_response and
                event.content.parts[0].function_response.name == "run_fun_fact_generation"):
                
                # The event log shows the data is in the 'result' key of the response dictionary
                response_dict = event.content.parts[0].function_response.response
                final_facts_json_string = response_dict.get('result')
                break # We found what we need, we can exit the loop

        if final_facts_json_string:
            final_facts = json.loads(final_facts_json_string)
            print("--- API: Successfully generated and parsed fun facts. ---")
            return jsonify(final_facts)
        else:
            print("--- API Error: Did not receive a valid response from the orchestrator tool. ---")
            return jsonify({"error": "Failed to get a response from the fun fact orchestrator tool."}), 500

    except Exception as e:
        print(f"--- API Error: {e} ---")
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

@app.route("/api/get_novel_content")
def get_novel_content():
    """
    Acts as a secure proxy to fetch prepared novel content from GCS.
    """
    # These environment variables are set by the Cloud Run service configuration
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    source_file_name = os.environ.get("GCS_FILE_NAME")

    if not all([bucket_name, source_file_name]):
        return jsonify({"error": "Server is not configured with GCS_BUCKET_NAME and GCS_FILE_NAME."}), 500

    # Construct the name of the prepared file based on the source file name
    prepared_file_name = source_file_name.replace('.txt', '_prepared.json')

    print(f"--- API Proxy: Fetching gs://{bucket_name}/{prepared_file_name} ---")
    
    # Use the robust tool function we already wrote
    content = read_text_from_gcs(bucket_name, prepared_file_name)

    if content.startswith("Error:"):
        return jsonify({"error": content}), 500

    # The content is already a JSON string, so we can return it directly
    # after parsing and re-dumping to ensure it's valid JSON.
    try:
        data = json.loads(content)
        return jsonify(data)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse novel content as JSON."}), 500

if __name__ == '__main__':
    # For local development. For production, use a WSGI server like Gunicorn.
    app.run(debug=True, port=5001) 
