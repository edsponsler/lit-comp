# decon/data_analysis/orchestrator.py 

import json
from decon.data_analysis.tools.micro_task_board_tool import post_micro_entry, get_micro_entries
from decon.data_analysis.lib.data_analysis_micro_agents import extract_keywords, segment_sentences

def run_data_analysis_agency(text_to_analyze: str, session_id: str, agency_task_id: str) -> dict:
    print("--- Orchestrator: Starting Data Analysis Agency ---")
    
    print("--- Orchestrator: Phase 1 - Segmentation ---")
    sentences_data = segment_sentences(text_to_analyze)
    sentences = sentences_data.get("sentences", [])
    print(f"--- Orchestrator: Segmented into {len(sentences)} sentences. ---")

    print("--- Orchestrator: Phase 2 - Posting Sentence Tasks ---")
    for sentence in sentences:
        post_micro_entry(
            agency_task_id=agency_task_id, session_id=session_id,
            status='new_task', task_type='sentence_to_analyze',
           input_payload_dict={'sentence': sentence}
        )

    print("--- Orchestrator: Phase 3 - Keyword Extraction ---")
    tasks_result = get_micro_entries(agency_task_id=agency_task_id, status='new_task')
    tasks_to_process = tasks_result.get("data", [])
    for task in tasks_to_process:
        sentence = task.get("input_payload", {}).get("sentence", "")
        if not sentence: continue
        keywords_dict = extract_keywords(sentence)
        post_micro_entry(
            agency_task_id=agency_task_id, session_id=session_id,
            status='completed', task_type='keywords_extracted',
            input_data_ref=[task.get("entry_id")],
            output_payload_dict=keywords_dict
        )
        post_micro_entry(
            entry_id=task.get("entry_id"), agency_task_id=agency_task_id,
            session_id=session_id, status='processing_complete'
        )

    print("--- Orchestrator: Phase 4 - Synthesis ---")
    keyword_results_dict = get_micro_entries(agency_task_id=agency_task_id, task_type='keywords_extracted')
    keyword_results = keyword_results_dict.get("data", [])
    all_keywords = set()
    for result in keyword_results:
        keywords = result.get("output_payload", {}).get("keywords", [])
        all_keywords.update(keywords)

    final_report = {
        "summary": f"Analysis complete. Extracted keywords from {len(sentences)} sentences.",
        "keywords": sorted(list(all_keywords))
    }
    print("--- Orchestrator: Analysis Complete. ---")
    return final_report