import uuid
import json
import os
import redis
import vertexai
from flask import Flask, render_template, request, jsonify, redirect, url_for
from google.adk.runners import Runner
from google.api_core.exceptions import NotFound
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from literary_companion.tools.gcs_tool import read_gcs_object
from literary_companion.agents.fun_fact_adk_agents import FunFactCoordinatorAgent
from literary_companion.config import REDIS_HOST, REDIS_PORT, GCS_BUCKET_NAME
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize Vertex AI
vertexai.init()

# Initialize Redis Client
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()
    app.logger.info("--- Successfully connected to Redis. ---")
except redis.exceptions.ConnectionError as e:
    app.logger.error(f"--- Could not connect to Redis. Caching will be disabled. Error: {e} ---")
    redis_client = None

def get_book_data_from_cache_or_gcs(book_name):
    """Helper function to retrieve book data, using Redis cache if available."""
    cache_key = f"book:{book_name}"
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                app.logger.info(f"--- Cache hit for {cache_key}. Serving from Redis. ---")
                return json.loads(cached_data)
        except redis.exceptions.RedisError as e:
            app.logger.error(f"Redis GET failed for key '{cache_key}': {e}")

    app.logger.info(f"--- Cache miss for {cache_key}. Fetching from GCS. ---")
    if not GCS_BUCKET_NAME:
        raise ValueError("GCS_BUCKET_NAME not configured")

    prepared_file_name = book_name.replace('.txt', '_prepared.json')
    try:
        book_data_str = read_gcs_object(GCS_BUCKET_NAME, prepared_file_name)
        if redis_client:
            try:
                redis_client.set(cache_key, book_data_str, ex=3600)  # 1-hour expiry
            except redis.exceptions.RedisError as e:
                app.logger.error(f"Redis SET failed for key '{cache_key}': {e}")
        return json.loads(book_data_str)
    except Exception as e:
        app.logger.error(f"Failed to read or parse {prepared_file_name} from GCS: {e}")
        raise

@app.route('/')
def index():
    return redirect(url_for('literary_companion_page'))

session_service_lc = InMemorySessionService()

@app.route("/literary_companion")
def literary_companion_page():
    return render_template(
        "literary_companion/literary_companion.html",
        GCS_FILE_NAME=os.environ.get("GCS_FILE_NAME")
    )

@app.route("/api/get_book_metadata", methods=["POST"])
def get_book_metadata():
    """Returns metadata (paragraph and chapter structure) for a book."""
    book_name = request.get_json().get("book_name")
    if not book_name:
        return jsonify({"error": "Missing 'book_name'"}), 400

    try:
        book_data = get_book_data_from_cache_or_gcs(book_name)
        # Return all paragraph data without the text to keep the payload small
        metadata = {
            "paragraphs": [
                {k: v for k, v in p.items() if k not in ['original_text', 'translated_text']}
                for p in book_data.get("paragraphs", [])
            ]
        }
        return jsonify(metadata)
    except Exception as e:
        return jsonify({"error": f"Could not load book metadata for {book_name}: {e}"}), 500

@app.route("/api/get_book_chapter", methods=["POST"])
def get_book_chapter():
    """Fetches the text content of a specific chapter."""
    req_data = request.get_json()
    book_name = req_data.get("book_name")
    chapter_number = req_data.get("chapter_number")

    if not all([book_name, chapter_number is not None]):
        return jsonify({"error": "Missing 'book_name' or 'chapter_number'"}), 400

    try:
        book_data = get_book_data_from_cache_or_gcs(book_name)
        chapter_paragraphs = [
            p for p in book_data.get("paragraphs", [])
            if p.get("chapter_number") == int(chapter_number)
        ]
        return jsonify({"paragraphs": chapter_paragraphs})
    except Exception as e:
        return jsonify({"error": f"Could not load chapter {chapter_number} for {book_name}: {e}"}), 500


@app.route("/api/get_screenplay", methods=["POST"])
def get_screenplay():
    """Fetches the screenplay for a specific chapter."""
    req_data = request.get_json()
    book_name = req_data.get("book_name")
    chapter_number = req_data.get("chapter_number")

    if not all([book_name, chapter_number is not None]):
        return jsonify({"error": "Missing 'book_name' or 'chapter_number'"}), 400

    try:
        # The screenplay is stored in a folder named after the book, without the .txt extension.
        folder_name = book_name.replace('.txt', '')
        object_name = f"{folder_name}/chapter_{chapter_number}_screenplay.md"
        
        screenplay_content = read_gcs_object(GCS_BUCKET_NAME, object_name)
        return jsonify({"screenplay": screenplay_content})
    except NotFound:
        app.logger.info(f"Screenplay not found for chapter {chapter_number} of {book_name}. Returning 404.")
        # The frontend will handle this and display a user-friendly message.
        return jsonify({"error": "Screenplay not found"}), 404
    except Exception as e:
        app.logger.error(f"Failed to read screenplay for chapter {chapter_number} of {book_name}: {e}")
        return jsonify({"error": f"Could not load screenplay for chapter {chapter_number}"}), 500


@app.route("/generate_fun_facts", methods=["POST"])
async def generate_fun_facts():
    req_data = request.get_json()
    text_segment = req_data.get("text_segment")
    session_id = req_data.get("session_id")
    chapter_number = req_data.get("chapter_number")
    book_name = req_data.get("book_name")

    missing_fields = []
    if not text_segment: missing_fields.append("text_segment")
    if not session_id: missing_fields.append("session_id")
    if chapter_number is None: missing_fields.append("chapter_number")
    if not book_name: missing_fields.append("book_name")
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    app.logger.info("--- API: Received request for fun facts. ---")

    coordinator = FunFactCoordinatorAgent(
        fun_fact_types=["historical_context", "geographical_setting", "plot_points", "character_sentiments", "character_relationships"],
        book_name=book_name,
        chapter_number=int(chapter_number),
    )

    runner = Runner(agent=coordinator, app_name="literary-companion-adk", session_service=session_service_lc)
    user_id = f"user_{session_id}"
    adk_session_id = session_id

    session_service_lc.create_session(
        app_name="literary-companion-adk", user_id=user_id, session_id=adk_session_id, state={"text_segment": text_segment}
    )

    try:
        async for _ in runner.run_async(user_id=user_id, session_id=adk_session_id, new_message=Content(role="user", parts=[Part(text="Go.")])):
            pass
        final_session = session_service_lc.get_session(app_name="literary-companion-adk", user_id=user_id, session_id=adk_session_id)
        final_result = final_session.state.get("final_fun_facts", {})
        return jsonify(final_result)
    except Exception as e:
        app.logger.error(f"--- API Error in generate_fun_facts: {e} ---")
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 
