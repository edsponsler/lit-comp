import uuid
import json
import os
import vertexai
from flask import Flask, render_template, request, jsonify, redirect, url_for
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part 
from literary_companion.tools.gcs_tool import read_gcs_object
from literary_companion.agents.fun_fact_coordinator_v1 import fun_fact_coordinator
from dotenv import load_dotenv

load_dotenv() 

app = Flask(__name__)

# The Vertex AI library is initialized automatically by the client libraries
# reading the GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION environment
# variables. These are set for the Cloud Run service in deploy_cloud_run.sh.
# Calling vertexai.init() explicitly suppresses a deprecation warning and
# ensures the project and location are correctly configured for all library calls.
vertexai.init()

@app.route('/')
def index():
    """Redirects the root URL to the literary companion page."""
    return redirect(url_for('literary_companion_page'))

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
    chapter_number = req_data.get("chapter_number")
    paragraph_in_chapter = req_data.get("paragraph_in_chapter")
    last_paragraph_in_chapter = req_data.get("last_paragraph_in_chapter")
    book_title = os.environ.get("GCS_FILE_NAME", "unknown-book").replace(".txt", "")

    if not all([text_segment, session_id, chapter_number, paragraph_in_chapter, last_paragraph_in_chapter]):
        return jsonify({"error": "Missing required fields"}), 400

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
        f"Generate fun facts for {book_title}, chapter {chapter_number}, "
        f"paragraph {paragraph_in_chapter}. "
        f"last_paragraph_in_chapter: {last_paragraph_in_chapter}. "
        f"session_id: '{session_id}', agency_task_id: '{agency_task_id}'. "
        f"The text segment is: {text_segment}"
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
                # Type-check to ensure the response is a dictionary, which satisfies linters
                # and adds robustness, even though the ADK framework should always provide a dict.
                if isinstance(response_dict, dict):
                    final_facts_json_string = response_dict.get('result')
                else:
                    # This case is not expected, so we'll ensure the string is None.
                    final_facts_json_string = None
                break  # We found what we need, we can exit the loop

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

    # This explicit check serves as a type guard that static analyzers understand,
    # proving that neither variable is None before they are used further down.
    if not bucket_name or not source_file_name:
        error_msg = "Server is not configured with GCS_BUCKET_NAME and GCS_FILE_NAME."
        app.logger.error(f"API Error in get_novel_content: {error_msg}")
        return jsonify({"error": error_msg}), 500

    # Construct the name of the prepared file based on the source file name
    prepared_file_name = source_file_name.replace('.txt', '_prepared.json')

    print(f"--- API Proxy: Fetching gs://{bucket_name}/{prepared_file_name} ---")
    
    try:
        # Use the robust tool function we already wrote
        content = read_gcs_object(bucket_name, prepared_file_name)
        # The content is a JSON string, so we can parse it.
        data = json.loads(content)
        return jsonify(data)
    except (IOError, ConnectionError) as e:
        # Catches errors from the GCS tool, like file not found or client issues.
        app.logger.error(f"GCS access error in get_novel_content: {e}")
        return jsonify({"error": str(e)}), 500
    except json.JSONDecodeError:
        # Catches errors if the file content is not valid JSON.
        app.logger.error(f"JSON parsing error for gs://{bucket_name}/{prepared_file_name}")
        return jsonify({"error": "Failed to parse novel content as JSON."}), 500

if __name__ == '__main__':
    # For local development. For production, use a WSGI server like Gunicorn.
    app.run(debug=True, port=5001) 
