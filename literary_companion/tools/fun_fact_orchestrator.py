# literary_companion/tools/fun_fact_orchestrator.py

import json
import concurrent.futures
from google.adk.tools import FunctionTool
from literary_companion.lib import fun_fact_generators
from literary_companion.tools import fun_fact_micro_task_board_tool as task_board

def _generate_and_post_result(fact_type: str, text_segment: str, session_id: str, agency_task_id: str):
    """
    Helper function to process a single fun fact type and post its result.
    This function is designed to be run in a separate thread.
    """
    print(f"--- Orchestrator (Thread): Generating '{fact_type}'... ---")
    try:
        generator_function = getattr(fun_fact_generators, f"analyze_{fact_type}")
        result_payload = generator_function(text=text_segment)

        # Post the result back to the board as a 'completed' task
        task_board.post_micro_entry(
            agency_task_id=agency_task_id,
            session_id=session_id,
            status="completed",
            task_type=f"{fact_type}_result",
            output_payload=result_payload,
        )
        return f"Successfully processed {fact_type}"
    except Exception as e:
        print(f"--- Orchestrator (Thread) ERROR: Failed to process '{fact_type}': {e} ---")
        # Optionally, post an error status to the board
        task_board.post_micro_entry(
            agency_task_id=agency_task_id,
            session_id=session_id,
            status="error",
            task_type=f"{fact_type}_result",
            output_payload={"error": str(e)},
        )
        return f"Failed to process {fact_type}"

def run_fun_fact_generation(
    text_segment: str, session_id: str, agency_task_id: str
) -> str:
    """
    A deterministic, Python-driven orchestrator for generating fun facts.
    This function manages a micro-task workflow using a Firestore-backed board
    and executes generation tasks in parallel using a ThreadPoolExecutor.
    """
    print(f"--- Orchestrator: Starting fun fact generation for agency_task_id: {agency_task_id} ---")

    # 1. Define the types of fun facts to generate
    fun_fact_types = [
        "historical_context",
        "geographical_setting",
        "plot_points",
        "character_sentiments",
        "character_relationships",
    ]

    # 2. Post a 'new_task' for each fun fact type to the micro-task board
    for fact_type in fun_fact_types:
        task_board.post_micro_entry(
            agency_task_id=agency_task_id,
            session_id=session_id,
            status="new_task",
            task_type=fact_type,
            input_payload={"text": text_segment},
        )
    print(f"--- Orchestrator: Posted {len(fun_fact_types)} new tasks to the board. ---")

    # 3. Process each task type in PARALLEL using a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(fun_fact_types)) as executor:
        # Prepare future tasks for each fact type
        future_to_fact_type = {
            executor.submit(_generate_and_post_result, fact_type, text_segment, session_id, agency_task_id): fact_type
            for fact_type in fun_fact_types
        }
        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(future_to_fact_type):
            fact_type = future_to_fact_type[future]
            try:
                result = future.result()
                print(f"--- Orchestrator (Thread): Completed task for '{fact_type}' with result: {result} ---")
            except Exception as exc:
                print(f"--- Orchestrator (Thread): Task for '{fact_type}' generated an exception: {exc} ---")

    # 4. Aggregate the results from the board
    print("--- Orchestrator: Aggregating final results... ---")
    final_results = {}
    for fact_type in fun_fact_types:
        response = task_board.get_micro_entries(
            agency_task_id=agency_task_id, task_type=f"{fact_type}_result"
        )
        if response["status"] == "success" and response["entries"]:
            # Filter out any error entries if you added error handling
            entry_payload = response["entries"][0].get("output_payload")
            if "error" not in entry_payload:
                 final_results[fact_type] = entry_payload

    print("--- Orchestrator: Fun fact generation complete. ---")

    # 5. Return the aggregated results as a single JSON string
    return json.dumps(final_results)


# Expose the entire orchestration logic as a single, callable ADK tool
fun_fact_orchestrator_tool = FunctionTool(run_fun_fact_generation)