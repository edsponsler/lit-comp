# Architecture Reference for decon/data-analysis

This document outlines the architecture of the `decon/data-analysis` branch, which provides a system for performing text analysis tasks.

## 1. Overview

The system is designed to process textual input, extract insights (specifically keywords), and make the results available via a task board. It employs a combination of ADK (Agent Development Kit) agents and a deterministic Python orchestrator, using Firestore as a backend for task management and communication between components.

The primary workflow involves a specialist agent that delegates the core analysis to a Python-based orchestrator. This orchestrator breaks down the analysis into smaller steps (sentence segmentation, keyword extraction per sentence) and uses a "micro-task board" (Firestore collection) to manage the state and results of these sub-tasks.

## 2. Key Components

### 2.1. Orchestrator (`decon/data_analysis/orchestrator.py`)

-   **`run_data_analysis_agency(text_to_analyze: str, session_id: str, agency_task_id: str) -> dict`**:
    -   This is the heart of the deterministic data analysis pipeline. It does not involve LLM calls directly for its logic.
    -   **Responsibilities**:
        1.  **Sentence Segmentation**: Splits the input `text_to_analyze` into individual sentences using the `segment_sentences` utility function.
        2.  **Task Creation**: For each sentence, it posts a new task to the Micro-Task Board with `status='new_task'` and `task_type='sentence_to_analyze'`. The sentence itself is included in the `input_payload_dict`.
        3.  **Keyword Extraction**: It retrieves the `sentence_to_analyze` tasks from the board. For each sentence, it calls the `extract_keywords` utility function.
        4.  **Result Posting**: The extracted keywords (a dictionary) are posted back to the Micro-Task Board as a new entry with `status='completed'`, `task_type='keywords_extracted'`, and a reference to the original sentence task. The original sentence task's status is then updated to `processing_complete`.
        5.  **Synthesis**: After processing all sentences, it retrieves all `keywords_extracted` entries from the board.
        6.  **Final Report**: It compiles a final report containing a summary message and a sorted list of all unique keywords extracted from the text.
    -   This orchestrator ensures a consistent and repeatable analysis process.

### 2.2. Agents

#### 2.2.1. `DataAnalysisSpecialist_v2` (`decon/data_analysis/agents/data_analysis_specialist_v2.py`)

-   **Type**: ADK Agent (`google.adk.agents.Agent`)
-   **Description**: "A specialist agent that uses a deterministic Python orchestrator to run a data analysis workflow and reports its status and final results to the Micro-Task board."
-   **Core Responsibilities**:
    1.  Receive a task (text to analyze, `session_id`, `task_id`).
    2.  Update its status on the Micro-Task Board to `'processing_analysis_request'` using the `post_micro_entry` tool.
    3.  Invoke the `run_data_analysis_agency` orchestrator with the provided text and IDs.
    4.  Upon completion, post the entire result dictionary from the orchestrator to the Micro-Task Board. This entry has `status='completed_analysis'` and includes the orchestrator's output in `output_payload_dict`.
    5.  Return a simple confirmation message to its caller.
-   **Tools**:
    -   `post_micro_entry` (from `micro_task_board_tool.py`): For updating the task board.
    -   `run_data_analysis_agency` (from `orchestrator.py`): To execute the main analysis pipeline.

#### 2.2.2. `AgencyCoordinator_v1` (`decon/data_analysis/agents/agency_coordinator_agent.py`)

-   **Type**: ADK Agent (`google.adk.agents.Agent`)
-   **Description**: "Orchestrates data analysis by coordinating micro-agents via a Micro-Task Board."
-   **Current Implementation**:
    -   The agent's instruction prompt (`AGENCY_COORDINATOR_INSTRUCTION`) is currently very simple and appears to be for debugging purposes. It instructs the agent to call the `segment_sentences_tool` and return its dictionary output.
    -   This suggests that its intended role as a higher-level coordinator is not fully implemented or is designed to be flexible.
-   **Tools**:
    -   `post_micro_entry_tool`: Wrapper for `post_micro_entry`.
    -   `get_micro_entries_tool`: Wrapper for `get_micro_entries`.
    -   `extract_keywords_tool`: Wrapper for `extract_keywords`.
    -   `segment_sentences_tool`: Wrapper for `segment_sentences`.
-   **Note**: While equipped with various tools, its current prompt limits its actions significantly.

### 2.3. Micro-Agents (Utility Functions) (`decon/data_analysis/lib/data_analysis_micro_agents.py`)

These are not ADK agents but rather Python functions that perform discrete, well-defined tasks. They are utilized by the orchestrator and can also be equipped as tools for ADK agents.

-   **`extract_keywords(text_input: str) -> dict`**:
    -   Takes a string, converts it to lowercase, removes punctuation, splits it into words, and filters out stopwords and short words.
    -   Returns a dictionary: `{"keywords": ["list", "of", "unique", "keywords"]}`.
-   **`segment_sentences(text_input: str) -> dict`**:
    -   Takes a string and splits it into sentences using regular expressions.
    -   Returns a dictionary: `{"sentences": ["list", "of", "sentences"]}`.

### 2.4. Micro-Task Board (`decon/data_analysis/tools/micro_task_board_tool.py`)

This module provides the interface to a Firestore database acting as a task management system.

-   **Firestore Collection**: `micro_task_board_cda`
-   **`_get_firestore_client()`**: Initializes and returns a Firestore client.
-   **`post_micro_entry(...)`**:
    -   Creates or updates an entry (document) on the board.
    -   Each entry is identified by a unique `entry_id` (auto-generated if not provided).
    -   Key fields include: `agency_task_id`, `session_id`, `status` (e.g., `new_task`, `completed`, `processing_analysis_request`), `task_type` (e.g., `sentence_to_analyze`, `keywords_extracted`), `input_payload_dict`, `output_payload_dict`, `posted_timestamp`, etc.
    -   Allows for direct passing of Python dictionaries for payloads.
-   **`get_micro_entries(...)`**:
    -   Retrieves entries from the board based on filters like `agency_task_id`, `session_id`, `status`, `task_type`.
    -   Results are ordered by `posted_timestamp`.
-   **`_make_serializable(...)`**: Helper function to ensure data (like timestamps) is Firestore-compatible before writing.

## 3. Data Flow and Interactions

The primary data flow for an analysis task is as follows:

1.  **Initiation**: An external system or agent initiates a data analysis task, providing text, a `session_id`, and an `agency_task_id` to the `DataAnalysisSpecialist_v2` agent.

2.  **Task Acknowledgement (DataAnalysisSpecialist_v2)**:
    -   `DataAnalysisSpecialist_v2` calls `post_micro_entry` to log its status as `'processing_analysis_request'` on the Micro-Task Board, associated with the given `session_id` and `agency_task_id`.

3.  **Delegation to Orchestrator (DataAnalysisSpecialist_v2 -> Orchestrator)**:
    -   `DataAnalysisSpecialist_v2` calls `run_data_analysis_agency` (from `orchestrator.py`), passing the text, `session_id`, and `agency_task_id`.

4.  **Orchestration Phase (within `run_data_analysis_agency`)**:
    a.  **Sentence Segmentation**:
        -   The orchestrator calls `segment_sentences(text_to_analyze)`.
    b.  **Sentence Task Posting**:
        -   For each sentence: The orchestrator calls `post_micro_entry` to create a task on the board:
            -   `status`: `'new_task'`
            -   `task_type`: `'sentence_to_analyze'`
            -   `input_payload_dict`: `{'sentence': 'The sentence text.'}`
            -   `agency_task_id`, `session_id` are propagated.
    c.  **Keyword Extraction per Sentence**:
        -   The orchestrator calls `get_micro_entries` to fetch all tasks with `status='new_task'` and `agency_task_id`.
        -   For each fetched sentence task:
            i.  It calls `extract_keywords(sentence_text)`.
            ii. It calls `post_micro_entry` to log the result:
                -   `status`: `'completed'`
                -   `task_type`: `'keywords_extracted'`
                -   `input_data_ref`: `[original_sentence_task_entry_id]`
                -   `output_payload_dict`: `{'keywords': [...]}` (from `extract_keywords`)
            iii.It calls `post_micro_entry` again to update the original sentence task:
                -   `entry_id`: `original_sentence_task_entry_id`
                -   `status`: `'processing_complete'`
    d.  **Result Synthesis**:
        -   The orchestrator calls `get_micro_entries` to fetch all tasks with `task_type='keywords_extracted'` for the current `agency_task_id`.
        -   It aggregates all keywords from the `output_payload` of these tasks into a single unique list.
    e.  **Return to Specialist**: The orchestrator returns a dictionary containing a summary and the aggregated list of keywords.

5.  **Final Result Posting (DataAnalysisSpecialist_v2)**:
    -   `DataAnalysisSpecialist_v2` receives the result dictionary from the orchestrator.
    -   It calls `post_micro_entry` one last time:
        -   `status`: `'completed_analysis'`
        -   `output_payload_dict`: The entire result dictionary from the orchestrator.
        -   `agency_task_id`, `session_id` are propagated.

6.  **Confirmation (DataAnalysisSpecialist_v2)**:
    -   `DataAnalysisSpecialist_v2` returns a final confirmation message (e.g., "Analysis complete...") to its caller.

## 4. Purpose and Design Considerations

-   **Modularity**: The system is broken down into agents, an orchestrator, utility functions (micro-agents), and a task board tool. This promotes separation of concerns.
-   **Determinism via Orchestrator**: The core analysis logic within `run_data_analysis_agency` is deterministic Python code, ensuring predictable outputs for the same input.
-   **Asynchronous Task Management**: The Micro-Task Board (Firestore) allows for decoupling of task generation and processing. While the current orchestrator runs these steps sequentially, the board infrastructure could support more complex, parallel, or distributed workflows.
-   **Agent-Based Interaction**: ADK agents provide a higher-level interface to the system and can be integrated into larger agentic ecosystems.
-   **Extensibility**:
    -   New analysis steps can be added to the orchestrator.
    -   New micro-agent functions can be developed for different types of analysis.
    -   The `AgencyCoordinator_v1` could be developed further to manage multiple specialist agents or more complex interactions.

## 5. Potential Areas for Future Development

-   **Enhanced AgencyCoordinator_v1**: Develop the `AgencyCoordinator_v1` to handle more sophisticated orchestration logic, potentially involving multiple types of analysis or dynamic task assignment based on results from the board.
-   **Error Handling and Retry Mechanisms**: Implement more robust error handling within the orchestrator and agents, potentially using the task board to flag and manage failed sub-tasks.
-   **Parallel Processing**: Modify the orchestrator or introduce new components to process sentences or other sub-tasks in parallel, leveraging the asynchronous nature of the Micro-Task Board.
-   **Configuration Management**: Externalize configurations (e.g., Firestore collection names, stopwords lists).
-   **Advanced NLP Techniques**: Integrate more advanced NLP libraries (e.g., spaCy, NLTK) into the `data_analysis_micro_agents` for improved sentence segmentation, keyword extraction, named entity recognition, etc.
```
