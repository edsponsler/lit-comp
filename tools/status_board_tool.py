# ~/projects/cie-0/tools/status_board_tool.py
from google.cloud import firestore
import datetime
import uuid
from google.adk.tools import FunctionTool # [cite: 231]
from typing import Optional

# Initialize Firestore DB client
# This will use Application Default Credentials or other configured credentials.
try:
    db = firestore.Client() # [cite: 235]
except Exception as e:
    print(f"Failed to initialize Firestore client: {e}. Make sure your environment is authenticated.")
    db = None

STATUS_BOARD_COLLECTION = "agent_status_board" # [cite: 235]

def update_status(
    agent_id: str,
    session_id: str,
    status: str,
    task_id: Optional[str] = None,
    status_details: Optional[str] = None, # [cite: 237]
    output_references: Optional[list] = None, # [cite: 237]
    input_references: Optional[list] = None, # [cite: 237]
    progress_metric: Optional[str] = None, # [cite: 237]
    dependencies: Optional[list] = None # [cite: 237]
) -> dict:
    """
    Creates or updates an agent's status entry on the Firestore Agent Status Board. [cite: 237]
    Args:
        agent_id (str): Unique identifier of the agent. [cite: 237]
        session_id (str): Identifier for the overall user session/report task. [cite: 237]
        status (str): Current status of the agent/task (e.g., "processing_request", "completed_task"). [cite: 238]
        task_id (str, optional): Unique identifier for the specific sub-task. [cite: 238]
        status_details (str, optional): A brief natural language description of the current activity. [cite: 239]
        output_references (list, optional): References to any output data produced. [cite: 240]
        input_references (list, optional): References to any input data the agent is using. [cite: 240]
        progress_metric (str, optional): Metric indicating progress (e.g., "3/5 sources processed"). [cite: 241]
        dependencies (list, optional): Task_ids that this task depends on. [cite: 241]
    Returns:
        dict: A dictionary containing the success status and the ID of the entry. [cite: 242]
    """
    if not db:
        return {"status": "error", "message": "Firestore client not initialized."} # [cite: 243]

    print(f"--- Tool: update_status called by {agent_id} for session {session_id}, task {task_id} with status {status} ---") # [cite: 243]

    # If task_id is provided, use it as the document ID for idempotency.
    # Otherwise, generate a new unique ID for the entry.
    entry_id = task_id if task_id else str(uuid.uuid4()) # [cite: 243]
    doc_ref = db.collection(STATUS_BOARD_COLLECTION).document(entry_id) # [cite: 243]

    log_data = {
        "timestamp": datetime.datetime.now(tz=datetime.timezone.utc), # [cite: 243]
        "agent_id": agent_id, # [cite: 244]
        "session_id": session_id, # [cite: 244]
        "task_id": task_id, # This will be the actual task_id, or None if not provided initially [cite: 244]
        "status": status, # [cite: 244]
        "entry_id": entry_id # Store the document ID explicitly for easier reference
    }
    if status_details:
        log_data["status_details"] = status_details # [cite: 244]
    if output_references:
        log_data["output_references"] = output_references # [cite: 244]
    if input_references:
        log_data["input_references"] = input_references # [cite: 244]
    if progress_metric:
        log_data["progress_metric"] = progress_metric # [cite: 245]
    if dependencies:
        log_data["dependencies"] = dependencies # [cite: 245]

    try:
        # Use set with merge=True to create or update parts of the document.
        # If entry_id is based on task_id, this will update the existing task status.
        doc_ref.set(log_data, merge=True) # [cite: 245]
        print(f"--- Tool: Status updated successfully for entry_id: {entry_id} (Task ID: {task_id}) ---") # [cite: 245]
        return {"status": "success", "entry_id": entry_id, "message": "Status updated successfully."} # [cite: 245]
    except Exception as e:
        print(f"--- Tool: Error updating status for entry_id {entry_id}: {e} ---") # [cite: 246]
        return {"status": "error", "entry_id": entry_id, "message": str(e)} # [cite: 246]

def get_status(session_id: str, task_id: Optional[str] = None, agent_id: Optional[str] = None) -> dict:
    """
    Queries Firestore for the status of a specific task, all tasks for an agent in a session,
    or all tasks in a session. [cite: 246]
    Args:
        session_id (str): Identifier for the overall user session. [cite: 247]
        task_id (str, optional): Specific task_id to retrieve. If provided, agent_id is ignored. [cite: 248]
                                 This assumes task_id was used as the document ID.
        agent_id (str, optional): Specific agent_id to retrieve status for within the session. [cite: 249]
    Returns:
        dict: A dictionary containing query status and a list of matching status entries. [cite: 250]
    """
    if not db:
        return {"status": "error", "message": "Firestore client not initialized.", "results": []} # [cite: 251]

    print(f"--- Tool: get_status called for session {session_id}, task {task_id}, agent {agent_id} ---") # [cite: 251]

    query = db.collection(STATUS_BOARD_COLLECTION)

    if task_id:
        # If task_id is provided, we assume it's the document ID.
        doc_ref = query.document(task_id) # [cite: 251]
        doc = doc_ref.get() # [cite: 251]
        if doc.exists:
            entry = doc.to_dict()
            # Ensure the retrieved document actually belongs to the requested session_id
            if entry.get("session_id") == session_id: # [cite: 252]
                print(f"--- Tool: Status retrieved for task_id: {task_id} ---") # [cite: 252]
                return {"status": "success", "results": [entry]} # [cite: 252]
            else:
                # Document with this task_id exists but for a different session
                print(f"--- Tool: Task ID {task_id} found, but not for session {session_id} ---") # [cite: 253]
                return {"status": "success", "results": [], "message": f"Task {task_id} not found in session {session_id}."} # [cite: 253]
        else:
            print(f"--- Tool: No status entry found for task_id: {task_id} ---") # [cite: 253]
            return {"status": "success", "results": [], "message": f"No status entry found for task_id: {task_id}."} # [cite: 253]

    # If task_id is not provided, filter by session_id and optionally agent_id
    query = query.where("session_id", "==", session_id) # [cite: 251]
    if agent_id:
        query = query.where("agent_id", "==", agent_id) # [cite: 254]

    try:
        # Order by timestamp to get the most recent updates first if querying multiple entries
        results = [doc.to_dict() for doc in query.order_by("timestamp", direction=firestore.Query.DESCENDING).stream()] # [cite: 254]
        print(f"--- Tool: Found {len(results)} status entries for session {session_id}, agent {agent_id or 'any'} ---") # [cite: 254]
        return {"status": "success", "results": results} # [cite: 254]
    except Exception as e:
        print(f"--- Tool: Error getting status: {e} ---") # [cite: 254]
        return {"status": "error", "message": str(e), "results": []} # [cite: 254]

# Create ADK FunctionTool instances
status_board_updater_tool = FunctionTool(update_status)

status_board_reader_tool = FunctionTool(get_status)

print("StatusBoardTool (updater and reader) defined.") # [cite: 256]