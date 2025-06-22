# app.py

import asyncio
import uuid
import os
import json
from flask import Flask, render_template, request, jsonify
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from google.cloud import tasks_v2
from google.auth.transport import requests as auth_requests
from google.oauth2 import id_token
from dotenv import load_dotenv

# --- Core Application Imports ---
# We ONLY import the top-level coordinator and the task board tool.
# The Coordinator will handle all the specialist agents.
from cie_core.agents.coordinator_agent import coordinator_agent
from decon.data_analysis.tools.micro_task_board_tool import post_micro_entry, get_micro_entries

# --- App Initialization and Configuration ---
load_dotenv()
app = Flask(__name__, template_folder='cie_core/templates')
TASKS_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
TASKS_LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION')
TASKS_QUEUE = os.getenv('TASKS_QUEUE_NAME', 'data-analysis-queue')
SERVICE_URL = os.getenv('SERVICE_URL')
session_service = InMemorySessionService()
APP_NAME = "cie_web_app"

# --- Endpoints ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
async def process_query():
    """ This endpoint accepts a user query and starts the main report generation task. """
    try:
        data = request.get_json()
        user_query_topic = data.get('query')
        if not user_query_topic: return jsonify({"message": "Query cannot be empty."}), 400
        
        agency_task_id = f"main_report_task_{user_query_topic.lower().replace(' ','_')[:10]}_{str(uuid.uuid4())[:4]}"
        session_id = f"session_{str(uuid.uuid4())}"
        
        # Use 'input_payload_dict' instead of 'input_payload_json'.
        post_micro_entry(
            agency_task_id=agency_task_id,
            session_id=session_id,
            status='accepted',
            task_type='main_report_task',
            input_payload_dict={"user_query": user_query_topic}
        )
        
        tasks_client = tasks_v2.CloudTasksClient()
        task_payload = {"agency_task_id": agency_task_id, "session_id": session_id, "user_query_topic": user_query_topic}
        invoker_sa_email = f"tasks-invoker-sa@{TASKS_PROJECT_ID}.iam.gserviceaccount.com"
        
        task = {"http_request": {
            "http_method": tasks_v2.HttpMethod.POST, "url": f"{SERVICE_URL}/run-task",
            "headers": {"Content-type": "application/json"}, "body": json.dumps(task_payload).encode(),
            "oidc_token": {"service_account_email": invoker_sa_email}
          },
          "dispatch_deadline": {
              "seconds": 600
          }
        }
        
        parent = tasks_client.queue_path(TASKS_PROJECT_ID, TASKS_LOCATION, TASKS_QUEUE)
        tasks_client.create_task(parent=parent, task=task)
        
        return jsonify({"message": "Request accepted for processing.","task_id": agency_task_id}), 202
    except Exception as e:
        print(f"Error in /process: {e}")
        return jsonify({"message": f"An internal error occurred: {str(e)}"}), 500

@app.route('/run-task', methods=['POST'])
async def run_task():
    """ This endpoint now correctly invokes the CoordinatorAgent and lets IT handle the workflow. """
    agency_task_id, session_id = "unknown", "unknown"
    try:
        id_token.verify_oauth2_token(request.headers.get("Authorization").split(" ")[1], auth_requests.Request(), audience=f"{SERVICE_URL}/run-task")
        
        task_data = request.get_json()
        agency_task_id, session_id, user_query_topic = task_data.get('agency_task_id'), task_data.get('session_id'), task_data.get('user_query_topic')
        current_user_id = f"user_{str(uuid.uuid4())}"
        session_service.create_session(app_name=APP_NAME, user_id=current_user_id, session_id=session_id)
        
        # Immediately update the main task's status so the UI knows we've started processing.
        post_micro_entry(entry_id=agency_task_id, agency_task_id=agency_task_id, session_id=session_id, status='processing')
        
        print(f"--- /run-task: Handing off to CoordinatorAgent for: {agency_task_id} ---")
        runner_coordinator = Runner(agent=coordinator_agent, app_name=APP_NAME, session_service=session_service)
        coordinator_query_text = f"User Query: Generate a report on '{user_query_topic}'.\nPlease use session_id: {session_id} for all your operations."
        initial_content = genai_types.Content(role='user', parts=[genai_types.Part(text=coordinator_query_text)])
        
        final_report_text = ""
        async for event in runner_coordinator.run_async(user_id=current_user_id, session_id=session_id, new_message=initial_content):
            if event.is_final_response() and event.content and event.content.parts and event.content.parts[0].text:
                final_report_text = event.content.parts[0].text
                break
        
        if not final_report_text:
            raise Exception("CoordinatorAgent did not produce a final report.")

        post_micro_entry(
            entry_id=agency_task_id, agency_task_id=agency_task_id,
            session_id=session_id, status='completed',
            output_payload_dict={'report': final_report_text}
        )
        
        print(f"--- /run-task: CoordinatorAgent finished for agency_task_id: {agency_task_id} ---")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error in /run-task: {e}")
        if agency_task_id != "unknown":
            post_micro_entry(entry_id=agency_task_id, agency_task_id=agency_task_id, session_id=session_id, status='error', error_details=str(e))
        return jsonify({"message": f"An internal error occurred: {str(e)}"}), 500

@app.route('/status/<task_id>', methods=['GET'])
async def get_status(task_id: str):
    """ This endpoint retrieves the status of a specific task by its ID. """
    try:
        result = get_micro_entries(agency_task_id=task_id, limit=1)
        if result.get("status") == "success" and result.get("data"):
            return jsonify({"status": "success", "details": result["data"][0]}), 200
        return jsonify(result), 500
    except Exception as e:
        return jsonify({"message": f"An internal error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)