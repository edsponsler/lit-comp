# decon/data_analysis/tools/micro_task_board_tool.py

import datetime
import uuid
import json
from typing import Optional, Dict, Any, List
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

db = None

def _get_firestore_client():
    global db
    if db is None:
        try:
            db = firestore.Client()
            print("--- Tool: Firestore client for Micro-Task Board initialized. ---")
        except Exception as e:
            print(f"--- Tool: CRITICAL Failed to initialize Firestore client: {e} ---")
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
    # --- accept dictionaries directly ---
    input_payload_dict: Optional[Dict[str, Any]] = None,
    output_payload_dict: Optional[Dict[str, Any]] = None,
    error_details: Optional[str] = None,
    trigger_conditions: Optional[List[str]] = None,
    entry_id: Optional[str] = None
) -> dict:
    """Creates or updates an entry, accepting Python dicts directly for payloads."""
    client = _get_firestore_client()
    if not client:
        return {"status": "error", "message": "Firestore client not available."}

    if not entry_id:
        entry_id = f"micro_entry_{uuid.uuid4()}"

    log_data = {
        "entry_id": entry_id, "agency_task_id": agency_task_id,
        "session_id": session_id, "micro_agent_id": micro_agent_id,
        "posted_timestamp": firestore.SERVER_TIMESTAMP, "status": status,
        "task_type": task_type, "input_data_ref": input_data_ref,
        # --- Use the dictionaries directly ---
        "input_payload": input_payload_dict,
        "output_payload": output_payload_dict,
        "error_details": error_details, "trigger_conditions": trigger_conditions,
    }
    log_data = {k: v for k, v in log_data.items() if v is not None}
    try:
        doc_ref = client.collection("micro_task_board_cda").document(entry_id)
        doc_ref.set(log_data, merge=True)
        print(f"--- Tool: Micro-Task Board entry '{entry_id}' posted/updated. Status: {status} ---")
        return {"status": "success", "entry_id": entry_id}
    except Exception as e:
        print(f"--- Tool: Error posting entry '{entry_id}': {e} ---")
        return {"status": "error", "entry_id": entry_id, "message": str(e)}

def get_micro_entries(
    agency_task_id: Optional[str] = None,
    session_id: Optional[str] = None,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    micro_agent_id: Optional[str] = None,
    limit: Optional[int] = 20
) -> dict:
    client = _get_firestore_client()
    if not client: return {"status": "error", "message": "Firestore client not available."}
    try:
        query = client.collection("micro_task_board_cda")
        if agency_task_id: query = query.where(filter=FieldFilter("agency_task_id", "==", agency_task_id))
        if session_id: query = query.where(filter=FieldFilter("session_id", "==", session_id))
        if status: query = query.where(filter=FieldFilter("status", "==", status))
        if task_type: query = query.where(filter=FieldFilter("task_type", "==", task_type))
        if micro_agent_id: query = query.where(filter=FieldFilter("micro_agent_id", "==", micro_agent_id))
        query = query.order_by("posted_timestamp", direction=firestore.Query.DESCENDING)
        if limit: query = query.limit(limit)
        results = [_make_serializable(doc.to_dict()) for doc in query.stream()]
        return {"status": "success", "data": results}
    except Exception as e:
        print(f"--- Tool: Error retrieving entries: {e} ---")
        return {"status": "error", "message": str(e), "data": []}