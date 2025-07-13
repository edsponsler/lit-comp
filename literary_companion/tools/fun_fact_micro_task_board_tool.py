# literary_companion/tools/fun_fact_micro_task_board_tool.py

import datetime
import uuid
import logging
from typing import Any, Dict, List, Optional
from google.cloud import firestore

# The collection name is specific to our new module, as per the outline 
MICRO_TASK_BOARD_COLLECTION = "fun_fact_micro_task_board"

# Configure logging for structured output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _get_firestore_client():
    """Helper to get the Firestore client."""
    try:
        db = firestore.Client()
        return db
    except Exception as e:
        logging.error("Error initializing Firestore client.", exc_info=True)
        return None

def _make_serializable(data: Any) -> Any:
    """Helper to make Firestore data JSON-serializable."""
    if isinstance(data, dict):
        return {k: _make_serializable(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_make_serializable(i) for i in data]
    if isinstance(data, (datetime.datetime, datetime.date)):
        return data.isoformat()
    return data

def post_micro_entry(
    agency_task_id: str,
    session_id: str,
    status: str,
    task_type: str,
    input_payload: Optional[Dict[str, Any]] = None,
    output_payload: Optional[Dict[str, Any]] = None,
    entry_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Posts or updates a micro-task entry on the Firestore board."""
    db = _get_firestore_client()
    if not db:
        return {"status": "error", "message": "Firestore client not available."}

    doc_id = entry_id or str(uuid.uuid4())
    doc_ref = db.collection(MICRO_TASK_BOARD_COLLECTION).document(doc_id)

    log_data = {
        "agency_task_id": agency_task_id,
        "session_id": session_id,
        "status": status,
        "task_type": task_type,
        "posted_timestamp": firestore.SERVER_TIMESTAMP,
        "entry_id": doc_id,
    }
    if input_payload:
        log_data["input_payload"] = input_payload
    if output_payload:
        log_data["output_payload"] = output_payload

    try:
        doc_ref.set(log_data, merge=True)
        return {"status": "success", "entry_id": doc_id}
    except Exception as e:
        logging.error("Error posting to micro-task board.", exc_info=True)
        return {"status": "error", "message": str(e)}

def get_micro_entries(
    agency_task_id: str,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Gets micro-task entries from the Firestore board for a given agency_task_id."""
    db = _get_firestore_client()
    if not db:
        return {"status": "error", "message": "Firestore client not available."}

    try:
        query = db.collection(MICRO_TASK_BOARD_COLLECTION).where("agency_task_id", "==", agency_task_id)
        if status:
            query = query.where("status", "==", status)
        if task_type:
            query = query.where("task_type", "==", task_type)

        results = [doc.to_dict() for doc in query.stream()]
        return {"status": "success", "entries": _make_serializable(results)}
    except Exception as e:
        logging.error("Error getting from micro-task board.", exc_info=True)
        return {"status": "error", "message": str(e), "entries": []}