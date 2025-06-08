import datetime
import uuid
from typing import Optional, Dict, Any, List
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Configuration
MICRO_TASK_BOARD_COLLECTION = "micro_task_board_cda"
db = None

def _get_firestore_client():
    """Initializes and returns the Firestore client."""
    global db
    if db is None:
        try:
            db = firestore.Client()
            print("--- Tool: Firestore client for Micro-Task Board initialized. ---")
        except Exception as e:
            print(f"--- Tool: CRITICAL Failed to initialize Firestore client for Micro-Task Board: {e} ---")
            # Depending on how critical this is, you might raise an exception
            # or ensure functions handle db being None.
    return db

def _make_serializable(data: Any) -> Any:
    """
    Recursively converts Firestore Timestamps and other non-serializable
    objects to a JSON-serializable format.
    (Similar to the one in status_board_tool.py)
    """
    if isinstance(data, list):
        return [_make_serializable(item) for item in data]
    if isinstance(data, dict):
        return {key: _make_serializable(value) for key, value in data.items()}
    if isinstance(data, (datetime.datetime, firestore.SERVER_TIMESTAMP.__class__)): # Handle SERVER_TIMESTAMP
        return data.isoformat() if hasattr(data, 'isoformat') else str(data) # Basic fallback
    # Add handling for google.api_core.datetime_helpers.DatetimeWithNanoseconds if needed
    # from google.api_core import datetime_helpers
    # if isinstance(data, datetime_helpers.DatetimeWithNanoseconds):
    #     return data.rfc3339()
    return data


def post_micro_entry(
    agency_task_id: str,
    session_id: str,
    status: str,
    micro_agent_id: Optional[str] = None,
    task_type: Optional[str] = None,
    input_data_ref: Optional[List[str]] = None,
    input_payload: Optional[Dict[str, Any]] = None,
    output_payload: Optional[Dict[str, Any]] = None,
    error_details: Optional[str] = None,
    trigger_conditions: Optional[List[str]] = None,
    entry_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates or updates an entry on the Micro-Task Board.
    """
    client = _get_firestore_client()
    if not client:
        return {"status": "error", "message": "Firestore client not available for Micro-Task Board."}

    if not entry_id:
        entry_id = f"micro_entry_{uuid.uuid4()}"

    log_data = {
        "entry_id": entry_id,
        "agency_task_id": agency_task_id,
        "session_id": session_id,
        "micro_agent_id": micro_agent_id,
        "posted_timestamp": firestore.SERVER_TIMESTAMP, # Let Firestore set the timestamp
        "status": status,
        "task_type": task_type,
        "input_data_ref": input_data_ref,
        "input_payload": input_payload,
        "output_payload": output_payload,
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
) -> Dict[str, Any]:
    """
    Retrieves entries from the Micro-Task Board based on query parameters.
    Orders by 'posted_timestamp' descending by default.
    """
    client = _get_firestore_client()
    if not client:
        return {"status": "error", "message": "Firestore client not available for Micro-Task Board."}

    try:
        query = client.collection(MICRO_TASK_BOARD_COLLECTION)

        if agency_task_id:
            query = query.where(filter=FieldFilter("agency_task_id", "==", agency_task_id))
        if session_id: # Though agency_task_id should be more specific if available
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

        results = []
        for doc in query.stream():
            results.append(_make_serializable(doc.to_dict()))

        print(f"--- Tool: Retrieved {len(results)} entries from Micro-Task Board matching query. ---")
        return {"status": "success", "data": results}
    except Exception as e:
        print(f"--- Tool: Error retrieving Micro-Task Board entries: {e} ---")
        return {"status": "error", "message": str(e), "data": []}

# We'll also need to wrap these as ADK FunctionTools later
# when we implement the Agency Coordinator.