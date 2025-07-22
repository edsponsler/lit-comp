import uuid
import json
import os
import vertexai
from flask import Flask, render_template, request, jsonify, redirect, url_for
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from literary_companion.tools.gcs_tool import read_gcs_object
from literary_companion.agents.fun_fact_adk_agents import FunFactCoordinatorAgent
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
    Receives user progress and runs the FunFactCoordinatorAgent.
    """
    req_data = request.get_json()
    # text_segment is no longer used from the request.
    # text_segment = req_data.get("text_segment")
    session_id = req_data.get("session_id")
    chapter_number = req_data.get("chapter_number")
    paragraph_in_chapter = req_data.get("paragraph_in_chapter")
    last_paragraph_in_chapter = req_data.get("last_paragraph_in_chapter")
    book_title = os.environ.get("GCS_FILE_NAME", "unknown-book").replace(".txt", "")

    # The text_segment is generated server-side, so it's removed from this check.
    if not all([session_id, chapter_number, paragraph_in_chapter, last_paragraph_in_chapter]):
        return jsonify({"error": "Missing required fields"}), 400

    print("--- API: Received request for fun facts. ---")

    # --- MODIFICATION: Start ---
    # Instead of using a specific paragraph, we will construct a text segment
    # based on the ENTIRE content of the current chapter.

    # 1. Get the prepared novel content from GCS
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    source_file_name = os.environ.get("GCS_FILE_NAME")

    if not bucket_name or not source_file_name:
        return jsonify({"error": "GCS bucket or file name not configured on server."}), 500

    prepared_file_name = source_file_name.replace('.txt', '_prepared.json')
    
    try:
        content_str = read_gcs_object(bucket_name, prepared_file_name)
        novel_data = json.loads(content_str)
    except Exception as e:
        print(f"--- API Error: Failed to read or parse novel content from GCS: {e} ---")
        return jsonify({"error": "Failed to load novel content."}), 500

    # 2. Extract all paragraphs of the current chapter
    try:
        # The prepared novel data has a flat list of paragraphs. We need to
        # filter them by the requested chapter_number to get the text for
        # the current chapter.
        target_chapter = int(chapter_number)
        current_chapter_paragraphs = [
            p["translated_text"]
            for p in novel_data.get("paragraphs", [])
            if p.get("chapter_number") == target_chapter
        ]

        if not current_chapter_paragraphs:
            return jsonify({"error": "Chapter has no paragraphs."}), 400

        # 3. Construct the new text segment by joining all paragraphs
        final_text_segment = "\n\n".join(current_chapter_paragraphs)
        print(f"--- API: Constructed text segment for fun facts from entire Chapter {chapter_number}. ---")

    except (ValueError, IndexError, KeyError) as e:
        print(f"--- API Error: Could not extract paragraphs: {e} ---")
        return jsonify({"error": "Failed to process chapter paragraphs."}), 500

    # --- MODIFICATION: End ---


    # 1. Define the fun fact types to generate
    fun_fact_types = [
        "historical_context",
        "geographical_setting",
        "plot_points",
        "character_sentiments",
        "character_relationships",
    ]

    # 2. Create the coordinator agent instance for this request
    coordinator = FunFactCoordinatorAgent(
        fun_fact_types=fun_fact_types,
        book_name=book_title,
        chapter_number=int(chapter_number),
    )

    # 3. Initialize the runner with the new agent
    runner = Runner(
        agent=coordinator,
        app_name="literary-companion-adk",
        session_service=session_service_lc,
    )

    user_id = f"user_{session_id}"
    # Use the session_id from the client as the ADK session_id
    adk_session_id = session_id

    # 4. Create a session with the initial state containing the new, full-chapter text segment
    initial_state = {"text_segment": final_text_segment}
    session_service_lc.create_session(
        app_name="literary-companion-adk", user_id=user_id, session_id=adk_session_id, state=initial_state
    )

    # 5. Run the agent
    initial_message = Content(role="user", parts=[Part(text="Generate fun facts.")])

    try:
        # Run the agent to completion by iterating through the events.
        async for event in runner.run_async(
            user_id=user_id, session_id=adk_session_id, new_message=initial_message
        ):
            pass  # We just need the agent to run; the result is in the state.

        # 6. Retrieve the final result from the session state
        final_session = session_service_lc.get_session(
            app_name="literary-companion-adk", user_id=user_id, session_id=adk_session_id
        )
        final_result = final_session.state.get("final_fun_facts", {})

        print("--- API: Successfully generated fun facts with ADK agent. ---")
        return jsonify(final_result)

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
