import datetime
import uuid
import json
from typing import Optional, Dict, Any, List
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Configuration
MICRO_TASK_BOARD_COLLECTION = "micro_task_board_cda"
db = None

def _get_firestore_client():
    global db
    if db is None:
        try:
            db = firestore.Client()
            print("--- Tool: Firestore client for Micro-Task Board initialized. ---")
        except Exception as e:
            print(f"--- Tool: CRITICAL Failed to initialize Firestore client for Micro-Task Board: {e} ---")
    return db

def _make_serializable(data: Any) -> Any:
    if isinstance(data, list):
        return [_make_serializable(item) for item in data]
    if isinstance(data, dict):
        return {key: _make_serializable(value) for key, value in data.items()}
    if isinstance(data, (datetime.datetime, firestore.SERVER_TIMESTAMP.__class__)):
        return data.isoformat() if hasattr(data, 'isoformat') else str(data)
    return data

def post_micro_entry(
    agency_task_id: str,
    session_id: str,
    status: str,
    micro_agent_id: Optional[str] = None,
    task_type: Optional[str] = None,
    input_data_ref: Optional[List[str]] = None,
    # These are JSON strings that will be parsed into dictionaries
    input_payload_json: Optional[str] = None,
    output_payload_json: Optional[str] = None,
    error_details: Optional[str] = None,
    trigger_conditions: Optional[List[str]] = None,
    entry_id: Optional[str] = None
) -> dict:
    """Creates or updates an entry on the Micro-Task Board.

    This function was deliberately refactored to accept complex payloads
    (input_payload_json, output_payload_json) as JSON strings. This design
    choice creates a simple and robust "contract" for the ADK FunctionTool.
    By using strings, we avoid potential API errors that can arise from
    the automatic schema generation of complex dictionary type hints,
    ensuring maximum reliability when this tool is used by an LLM agent.
    The function itself handles the safe decoding of these JSON strings.
    """
    client = _get_firestore_client()
    if not client:
        return {"status": "error", "message": "Firestore client not available."}

    # Parse the JSON strings into dictionaries
    try:
        input_payload = json.loads(input_payload_json) if input_payload_json else None
        output_payload = json.loads(output_payload_json) if output_payload_json else None
    except json.JSONDecodeError as e:
        print(f"--- Tool: Error decoding JSON payload: {e} ---")
        return {"status": "error", "message": f"Invalid JSON payload provided: {e}"}

    # Use the newly parsed payload variables.
    if not entry_id:
        entry_id = f"micro_entry_{uuid.uuid4()}"

    log_data = {
        "entry_id": entry_id,
        "agency_task_id": agency_task_id,
        "session_id": session_id,
        "micro_agent_id": micro_agent_id,
        "posted_timestamp": firestore.SERVER_TIMESTAMP,
        "status": status,
        "task_type": task_type,
        "input_data_ref": input_data_ref,
        "input_payload": input_payload, # Use the parsed variable
        "output_payload": output_payload, # Use the parsed variable
        "error_details": error_details,
        "trigger_conditions": trigger_conditions,
    }

    # Remove None fields to keep documents clean
    log_data = {k: v for k, v in log_data.items() if v is not None}

    try:
        doc_ref = client.collection(MICRO_TASK_BOARD_COLLECTION).document(entry_id)
        doc_ref.set(log_data, merge=True) # merge=True allows incremental updates
        print(f"--- Tool: Micro-Task Board entry '{entry_id}' for agency_task_id '{agency_task_id}' posted/updated. Status: {status} ---")
        return {"status": "success", "entry_id": entry_id, "message": "Entry posted successfully."}
    except Exception as e:
        print(f"--- Tool: Error posting Micro-Task Board entry '{entry_id}': {e} ---")
        return {"status": "error", "entry_id": entry_id, "message": str(e)}

def get_micro_entries(
    agency_task_id: Optional[str] = None,
    session_id: Optional[str] = None,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    micro_agent_id: Optional[str] = None,
    limit: Optional[int] = 20
) -> dict:
    """Retrieves entries from the Micro-Task Board based on query parameters.

    As part of a robust design pattern for ADK tools, this function returns
    its findings as a single JSON string rather than a direct Python object.
    This maintains a consistent, simple, and reliable string-based contract
    with the calling LLM agent. The agent is then responsible for parsing
    this string to use the data, keeping the tool's interface with the
    underlying API as clean as possible.
    """
    client = _get_firestore_client()
    if not client:
        return {"status": "error", "message": "Firestore client not available."}
    try:
        query = client.collection(MICRO_TASK_BOARD_COLLECTION)
        if agency_task_id:
            query = query.where(filter=FieldFilter("agency_task_id", "==", agency_task_id))
        if session_id:
            query = query.where(filter=FieldFilter("session_id", "==", session_id))
        if status:
            query = query.where(filter=FieldFilter("status", "==", status))
        if task_type:
            query = query.where(filter=FieldFilter("task_type", "==", task_type))
        if micro_agent_id:
            query = query.where(filter=FieldFilter("micro_agent_id", "==", micro_agent_id))

        query = query.order_by("posted_timestamp", direction=firestore.Query.DESCENDING)
        if limit:
            query = query.limit(limit)
        results = [
            _make_serializable(doc.to_dict()) for doc in query.stream()
        ]
        return {"status": "success", "data": results}
    except Exception as e:
        print(f"--- Tool: Error retrieving Micro-Task Board entries: {e} ---")
        return {"status": "error", "message": str(e), "data": []}