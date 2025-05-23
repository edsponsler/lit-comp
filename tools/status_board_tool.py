# ~/projects/cie-0/tools/status_board_tool.py
from google.cloud import firestore
import datetime
import uuid
from google.adk.tools import FunctionTool
from typing import Optional, List, Dict, Any, Union # Ensure all necessary typing imports

# Attempt to import DatetimeWithNanoseconds for robust type checking
# This is often found in google.api_core.datetime_helpers
try:
    from google.api_core.datetime_helpers import DatetimeWithNanoseconds
except ImportError:
    print("Warning: DatetimeWithNanoseconds from google.api_core.datetime_helpers could not be imported. "
          "The serialization logic will primarily rely on datetime.datetime checks.")
    # Create a dummy class so isinstance check doesn't fail if import is missing
    class DatetimeWithNanoseconds(object): pass

# Initialize Firestore DB client
db = None
try:
    db = firestore.Client()
except Exception as e:
    print(f"CRITICAL: Failed to initialize Firestore client: {e}. "
          "Ensure your GCP project is set up and authenticated (gcloud auth application-default login).")
    # Optionally, re-raise or exit if Firestore is critical for the module to function
    # For now, functions will return an error if db is None.

STATUS_BOARD_COLLECTION = "agent_status_board"

def _make_serializable(data: Any) -> Any:
    """
    Recursively converts datetime.datetime and DatetimeWithNanoseconds objects
    in data to ISO 8601 strings for JSON serialization.
    """
    if isinstance(data, list):
        return [_make_serializable(item) for item in data]
    elif isinstance(data, dict):
        return {key: _make_serializable(value) for key, value in data.items()}
    # Check for DatetimeWithNanoseconds first if its class was successfully imported and is not the dummy
    elif 'DatetimeWithNanoseconds' in globals() and DatetimeWithNanoseconds is not object and isinstance(data, DatetimeWithNanoseconds):
        return data.isoformat()
    # Then check for standard datetime.datetime (Firestore Timestamps usually convert to this)
    elif isinstance(data, datetime.datetime):
        return data.isoformat()
    return data

def update_status(
    agent_id: str,
    session_id: str,
    status: str,
    task_id: Optional[str] = None,
    status_details: Optional[str] = None,
    # output_references schema: Array of Strings/Objects [cite: 121]
    output_references: Optional[List[Dict[str, Any]]] = None, # More specific: List of Dicts
    # input_references schema: Array of Strings/Objects [cite: 120]
    input_references: Optional[List[Dict[str, Any]]] = None, # More specific: List of Dicts
    progress_metric: Optional[str] = None,
    dependencies: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Creates or updates an agent's status entry on the Firestore Agent Status Board.
    """
    if not db:
        return {"status": "error", "message": "Firestore client not initialized."}

    print(f"--- Tool: update_status called by {agent_id} for session {session_id}, task {task_id} with status {status} ---")

    entry_id = task_id if task_id else str(uuid.uuid4())
    doc_ref = db.collection(STATUS_BOARD_COLLECTION).document(entry_id)

    log_data: Dict[str, Any] = {
        "timestamp": datetime.datetime.now(tz=datetime.timezone.utc), # Stored as Firestore Timestamp
        "agent_id": agent_id,
        "session_id": session_id,
        "task_id": task_id,
        "status": status,
        "entry_id": entry_id
    }
    if status_details is not None:
        log_data["status_details"] = status_details
    if output_references is not None:
        # These are assumed to be JSON-serializable as passed by the LLM/agent
        log_data["output_references"] = output_references
    if input_references is not None:
        log_data["input_references"] = input_references
    if progress_metric is not None:
        log_data["progress_metric"] = progress_metric
    if dependencies is not None:
        log_data["dependencies"] = dependencies

    try:
        doc_ref.set(log_data, merge=True)
        print(f"--- Tool: Status updated successfully for entry_id: {entry_id} (Task ID: {task_id}) ---")
        return {"status": "success", "entry_id": entry_id, "message": "Status updated successfully."}
    except Exception as e:
        print(f"--- Tool: Error updating status for entry_id {entry_id}: {e} ---")
        return {"status": "error", "entry_id": entry_id, "message": str(e)}


def get_status(session_id: str, task_id: Optional[str] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Queries Firestore for the status of a specific task, all tasks for an agent in a session,
    or all tasks in a session. Returns JSON serializable data.
    """
    if not db:
        return {"status": "error", "message": "Firestore client not initialized.", "results": []}

    print(f"--- Tool: get_status called for session {session_id}, task {task_id}, agent {agent_id} ---")
    query = db.collection(STATUS_BOARD_COLLECTION)

    results_to_serialize: List[Dict[str, Any]] = []

    if task_id:
        doc_ref = query.document(task_id)
        doc = doc_ref.get()
        if doc.exists:
            entry = doc.to_dict()
            if entry and entry.get("session_id") == session_id: # Check if entry is not None
                print(f"--- Tool: Status retrieved for task_id: {task_id} ---")
                results_to_serialize.append(entry)
            else:
                print(f"--- Tool: Task ID {task_id} found, but not for session {session_id} or entry data is invalid ---")
                # Return structure consistent with multiple results, even if empty or message
                return {"status": "success", "results": [], "message": f"Task {task_id} not found in session {session_id} or entry data is invalid."}
        else:
            print(f"--- Tool: No status entry found for task_id: {task_id} ---")
            return {"status": "success", "results": [], "message": f"No status entry found for task_id: {task_id}."}
    else:
        # If no specific task_id, query by session_id and optionally agent_id
        query = query.where("session_id", "==", session_id)
        if agent_id:
            query = query.where("agent_id", "==", agent_id)
        
        try:
            for doc_snap in query.order_by("timestamp", direction=firestore.Query.DESCENDING).stream():
                if doc_snap.exists:
                    results_to_serialize.append(doc_snap.to_dict())
        except Exception as e:
            print(f"--- Tool: Error querying status: {e} ---")
            return {"status": "error", "message": str(e), "results": []}

    serializable_results = _make_serializable(results_to_serialize)
    print(f"--- Tool: Found {len(serializable_results)} status entries for session {session_id}, agent {agent_id or 'any'} ---")
    return {"status": "success", "results": serializable_results}


# Create ADK FunctionTool instances
status_board_updater_tool = FunctionTool(update_status)
status_board_reader_tool = FunctionTool(get_status)

print("StatusBoardTool (updater and reader) defined with Optional typing and datetime serialization.")