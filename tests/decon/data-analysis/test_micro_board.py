# test_micro_board.py
import os
import uuid 

# Run with python -m tests.decon.data-analysis.test_micro_board from the project root
from decon.data_analysis.tools.micro_task_board_tool import post_micro_entry, get_micro_entries

# Ensure GOOGLE_CLOUD_PROJECT is set in your environment for Firestore
# os.environ["GOOGLE_CLOUD_PROJECT"] = "your-gcp-project-id"

if __name__ == "__main__":
    print("Testing Micro-Task Board with DYNAMIC IDs...")

    # --- DYNAMIC ID GENERATION ---
    # Generate unique IDs for this specific test run
    run_uuid = str(uuid.uuid4())
    test_session_id = f"session_test_{run_uuid}"
    test_agency_task_id = f"agency_task_test_{run_uuid}"
    # --- END DYNAMIC ID GENERATION ---

    # Test posting
    print(f"\nUsing agency_task_id: {test_agency_task_id}")
    print("Posting entry 1 (a new task)...")
    post_result1 = post_micro_entry(
        agency_task_id=test_agency_task_id,
        session_id=test_session_id,
        status="new_task",
        task_type="text_to_analyze",
        input_payload={"text": "This is the first text to analyze."},
        micro_agent_id="TestSystem"
    )
    
    print(f"Post Result 1: {post_result1}")
    entry1_id = post_result1.get("entry_id")

    if entry1_id:
        print("\nPosting entry 2 (output from a hypothetical micro-agent)...")
        post_result2 = post_micro_entry(
            agency_task_id=test_agency_task_id,
            session_id=test_session_id,
            status="completed",
            task_type="keywords_extracted",
            input_data_ref=[entry1_id], # Referencing the first task
            output_payload={"keywords": ["first", "text", "analyze"]},
            micro_agent_id="KeywordExtractorMicroAgent_Test"
        )
        print(f"Post Result 2: {post_result2}")

    # Test getting entries
    print(f"\nGetting all entries for agency_task_id '{test_agency_task_id}':")
    get_all_result = get_micro_entries(agency_task_id=test_agency_task_id)
    if get_all_result["status"] == "success":
        for entry in get_all_result["data"]:
            print(entry)

    print(f"\nGetting 'completed' entries for agency_task_id '{test_agency_task_id}':")
    get_completed_result = get_micro_entries(
        agency_task_id=test_agency_task_id,
        status="completed"
    )
    if get_completed_result["status"] == "success":
        for entry in get_completed_result["data"]:
            print(entry)

    print("\nMicro-Task Board test finished.")