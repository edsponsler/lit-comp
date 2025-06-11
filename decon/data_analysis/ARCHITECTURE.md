# Architectural Reference for decon/data-analysis
[CIE Wiki](https://github.com/edsponsler/cie-adk/wiki)
## 1. Overall Architecture

The `decon/data-analysis` module provides specialized services for performing detailed data analysis. Its primary purpose is to break down complex analysis tasks into smaller, manageable, and traceable units of work. This is achieved through a combination of deterministic orchestration, a micro-task management system, specialized agents, and core processing libraries.

The key components of this module are:

*   **Orchestrator (`orchestrator.py`)**: A Python-based deterministic workflow manager that controls the sequence of analysis operations.
*   **Micro-Task Board (`tools/micro_task_board_tool.py`)**: A Firestore-backed system for posting, tracking, and retrieving individual tasks (micro-tasks) within the analysis pipeline.
*   **Agents (`agents/`)**:
    *   `DataAnalysisSpecialist_v2`: An agent that provides a clean, high-level interface to the data analysis capabilities of this module.
    *   `AgencyCoordinator_agent` (Legacy): An older, LLM-based agent for coordinating micro-tasks, now largely superseded by the deterministic orchestrator for reliability.
*   **Libraries (`lib/`)**: Python modules containing the core logic for specific data manipulation tasks, such as sentence segmentation and keyword extraction.

This architecture emphasizes reliability, traceability, and modularity in handling data analysis requests.

## 2. Orchestrator (`orchestrator.py`)

The `orchestrator.py` script is central to the `decon/data-analysis` module. It provides a deterministic, Python-driven approach to managing the data analysis workflow, ensuring reliability and predictability.

### `run_data_analysis_agency` Function

This is the main function and entry point for initiating a data analysis task. It takes text input, a session ID, and an agency task ID, and returns a dictionary containing the analysis results.

The orchestration process involves several distinct phases:

1.  **Phase 1: Sentence Segmentation**:
    *   The input text is first segmented into individual sentences using the `segment_sentences` function from `lib/data_analysis_micro_agents.py`.

2.  **Phase 2: Task Posting to Micro-Task Board**:
    *   Each segmented sentence is then posted as a new micro-task to the Micro-Task Board.
    *   These tasks are marked with a status of `new_task` and a `task_type` of `sentence_to_analyze`.
    *   The `post_micro_entry` function from `tools/micro_task_board_tool.py` is used for this.

3.  **Phase 3: Keyword Extraction**:
    *   The orchestrator retrieves the `new_task` entries from the Micro-Task Board.
    *   For each sentence task, it calls the `extract_keywords` function (from `lib/data_analysis_micro_agents.py`) to identify significant keywords.
    *   The extracted keywords are then posted back to the Micro-Task Board as a `completed` task with `task_type` `keywords_extracted`.
    *   The original sentence task is updated to `processing_complete`.

4.  **Phase 4: Synthesis**:
    *   All `keywords_extracted` tasks associated with the current `agency_task_id` are retrieved from the board.
    *   The keywords from all processed sentences are aggregated into a single unique set.

5.  **Phase 5: Final Report Generation**:
    *   A final JSON report is constructed, containing a summary of the analysis (e.g., number of sentences processed) and the complete list of unique keywords extracted.

### Shift from LLM-based Coordination

It's important to note that this Python-based orchestrator (`run_data_analysis_agency`) was implemented to replace a previous LLM-based `AgencyCoordinator_agent`. This shift was made to enhance the reliability, determinism, and debuggability of the data analysis process. While the LLM-based coordinator offered flexibility, the direct Python orchestration provides more consistent and predictable behavior.

## 3. Micro-Task Board (`tools/micro_task_board_tool.py`)

The Micro-Task Board is a crucial component for managing the state and flow of individual tasks within the data analysis pipeline. It is implemented using Google Cloud Firestore, providing a persistent and scalable solution for task tracking.

### Purpose

The primary purpose of the Micro-Task Board is to:

*   Decouple different stages of the analysis process.
*   Allow for atomic units of work (micro-tasks) to be created, assigned, and tracked.
*   Persist the state of each micro-task, including inputs, outputs, and status.
*   Enable traceability and debugging by logging the progression of tasks.

### Key Functions

*   **`_get_firestore_client()`**: Initializes and returns a Firestore client instance.
*   **`post_micro_entry(...)`**: This function is responsible for creating new entries or updating existing ones on the board.
    *   It accepts various parameters including `agency_task_id`, `session_id`, `status`, `task_type`, `input_payload_json`, `output_payload_json`, etc.
    *   Payloads (`input_payload_json`, `output_payload_json`) are expected as JSON strings, which are then parsed into dictionaries before being stored in Firestore. This ensures reliable serialization.
    *   Each entry is assigned a unique `entry_id` if not provided.
    *   It records timestamps and handles potential errors during Firestore operations.
*   **`get_micro_entries(...)`**: This function retrieves entries from the board based on specified query parameters.
    *   Filtering can be done on `agency_task_id`, `session_id`, `status`, `task_type`, and `micro_agent_id`.
    *   Results are typically ordered by `posted_timestamp` and can be limited in number.
    *   It handles making Firestore data serializable (e.g., converting timestamps to ISO format) before returning.

### Task Entry Structure

A typical micro-task entry stored in the Firestore collection (`micro_task_board_cda`) includes fields such as:

*   `entry_id`: Unique identifier for the task entry.
*   `agency_task_id`: Identifier for the overall analysis agency task this micro-task belongs to.
*   `session_id`: Session identifier.
*   `micro_agent_id`: (Optional) Identifier of the agent responsible for this task.
*   `posted_timestamp`: Timestamp of when the entry was posted or last updated.
*   `status`: Current status of the task (e.g., `new_task`, `processing_complete`, `completed`, `error`).
*   `task_type`: Type of the task (e.g., `sentence_to_analyze`, `keywords_extracted`).
*   `input_data_ref`: (Optional) List of entry IDs that this task depends on.
*   `input_payload`: Dictionary containing the input data for the task.
*   `output_payload`: Dictionary containing the result/output of the task.
*   `error_details`: (Optional) Details of any error encountered during task processing.
*   `trigger_conditions`: (Optional) Conditions that might trigger this task.

The Micro-Task Board facilitates a clear and organized workflow, especially when multiple small operations need to be performed and tracked as part of a larger data analysis request.

## 4. Agents (`agents/`)

The `agents/` directory contains specialized agents that interact with the data analysis pipeline.

### `data_analysis_specialist_v2.py`

*   **Name**: `DataAnalysisSpecialist_v2`
*   **Purpose**: This agent serves as a high-level interface to the deterministic data analysis workflow. Its primary responsibility is to simplify the invocation of the analysis process for external systems or callers.
*   **Functionality**:
    *   It is a simple agent equipped with a single tool: `run_data_analysis_agency_tool`.
    *   This tool is a wrapper around the `run_data_analysis_agency` function from `orchestrator.py`.
    *   When this agent receives a request (typically text to be analyzed), its instruction is to call the `run_data_analysis_agency_tool`.
    *   The result from the orchestrator (a dictionary) is then returned as the final response of the agent.
*   **Model**: Uses `DEFAULT_AGENT_MODEL` from `cie_core.config`.
*   **Key Characteristic**: It abstracts the complexity of the underlying orchestration and micro-task management, providing a clean entry point for data analysis tasks.

### `agency_coordinator_agent.py` (Legacy/Alternative)

*   **Name**: `DataAnalysisAgencyCoordinator_v1`
*   **Purpose**: This agent represents an earlier or alternative approach to orchestrating data analysis tasks using an LLM.
*   **Functionality**:
    *   It was designed to coordinate "micro-agents" (like `extract_keywords` and `segment_sentences`) by using tools to interact with the Micro-Task Board.
    *   For example, it might first call a tool to segment sentences, then post these sentences to the board, then trigger keyword extraction for each.
    *   It is equipped with tools such as `post_micro_entry_tool`, `get_micro_entries_tool`, `extract_keywords_tool`, and `segment_sentences_tool`. These tools are wrappers around functions from `micro_task_board_tool.py` and `data_analysis_micro_agents.py`.
*   **Model**: Uses `DEFAULT_AGENT_MODEL`.
*   **Current Status**: As indicated by comments in `orchestrator.py` and the design of `DataAnalysisSpecialist_v2`, this LLM-based coordinator has largely been superseded by the deterministic Python orchestrator (`run_data_analysis_agency`) for core operations, primarily to improve reliability and predictability. It might still exist for comparison, experimentation, or specific use cases where LLM-based dynamic coordination is preferred.

## 5. Libraries (`lib/data_analysis_micro_agents.py`)

The `lib/` directory, particularly `data_analysis_micro_agents.py`, houses the core Python functions that perform specific data manipulation tasks. These functions are the "micro-agents" or fundamental processing units called by the orchestrator or, in some cases, by LLM agents via tools.

### `data_analysis_micro_agents.py`

This file contains the actual implementation of the low-level data processing logic.

*   **`extract_keywords(text_input: str) -> dict`**:
    *   **Purpose**: To extract meaningful keywords from a given string of text.
    *   **Input**: A single string (`text_input`).
    *   **Processing**:
        1.  Converts the input text to lowercase.
        2.  Removes punctuation using regular expressions.
        3.  Splits the text into individual words.
        4.  Filters out common English "stopwords" (e.g., "a", "the", "is") based on a predefined list `STOPWORDS`.
        5.  Filters out words that are too short (length <= 2).
        6.  Returns a unique list of identified keywords.
    *   **Output**: A dictionary of the format `{"keywords": ["keyword1", "keyword2", ...]}`.
    *   **Note**: The `STOPWORDS` list is a basic one; for more advanced scenarios, a comprehensive list from libraries like NLTK or spaCy would be used.

*   **`segment_sentences(text_input: str) -> dict`**:
    *   **Purpose**: To segment a given block of text into individual sentences.
    *   **Input**: A single string (`text_input`).
    *   **Processing**:
        1.  Uses regular expressions (`re.split`) to identify sentence boundaries (typically based on punctuation like periods, question marks, and exclamation marks).
        2.  The regex `r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s'` is designed to handle common cases and avoid splitting on abbreviations (e.g., "Mr.", "Dr.").
        3.  Strips leading/trailing whitespace from each identified sentence.
        4.  Filters out any empty strings that might result from the split.
    *   **Output**: A dictionary of the format `{"sentences": ["sentence 1.", "sentence 2.", ...]}`.

These functions are designed to be pure and reusable, forming the building blocks for the more complex analysis orchestrated by `run_data_analysis_agency`.

## 6. Data Flow

The data flow within the `decon/data-analysis` module, when using the primary `DataAnalysisSpecialist_v2` and the deterministic orchestrator, can be summarized as follows:

1.  **Initial Request**:
    *   An external system or caller makes a request to the `DataAnalysisSpecialist_v2` agent, providing the raw text to be analyzed.

2.  **Agent Invocation**:
    *   The `DataAnalysisSpecialist_v2` agent, following its instructions, calls the `run_data_analysis_agency_tool`.

3.  **Orchestrator Execution (`run_data_analysis_agency`)**:
    *   The tool executes the `run_data_analysis_agency` function in `orchestrator.py`.
    *   **Sentence Segmentation**: The orchestrator calls `segment_sentences(text_input)` from `lib/data_analysis_micro_agents.py`.
        *   *Input*: Raw text.
        *   *Output*: A list of sentences.
    *   **Task Posting (Sentences)**: For each sentence:
        *   The orchestrator calls `post_micro_entry(...)` from `tools/micro_task_board_tool.py` to create a `sentence_to_analyze` task on the Micro-Task Board.
        *   *Input*: Sentence string, `agency_task_id`, `session_id`, status (`new_task`).
        *   *Output*: A new Firestore document representing the task.
    *   **Task Retrieval (for Keyword Extraction)**:
        *   The orchestrator calls `get_micro_entries(...)` to fetch all `new_task` entries of type `sentence_to_analyze` for the current `agency_task_id`.
    *   **Keyword Extraction**: For each retrieved sentence task:
        *   The orchestrator calls `extract_keywords(sentence)` from `lib/data_analysis_micro_agents.py`.
            *   *Input*: A single sentence.
            *   *Output*: A list of keywords for that sentence.
        *   **Task Posting (Keywords)**: The orchestrator calls `post_micro_entry(...)` to create a `keywords_extracted` task on the Micro-Task Board.
            *   *Input*: Extracted keywords, `agency_task_id`, `session_id`, status (`completed`), reference to the original sentence task.
            *   *Output*: A new Firestore document with keyword results.
        *   **Task Update (Sentence)**: The orchestrator calls `post_micro_entry(...)` again to update the status of the original sentence task to `processing_complete`.
    *   **Synthesis**:
        *   The orchestrator calls `get_micro_entries(...)` to retrieve all `keywords_extracted` tasks for the `agency_task_id`.
        *   It aggregates all keywords from these tasks into a unique set.
    *   **Final Report**: A JSON dictionary is compiled, containing a summary and the aggregated list of unique keywords.

4.  **Response to Agent**:
    *   The final report dictionary is returned by the `run_data_analysis_agency` function to the `run_data_analysis_agency_tool`.

5.  **Final Output**:
    *   The `DataAnalysisSpecialist_v2` agent returns this dictionary as its final response to the initial caller.

This flow ensures that each step of the analysis is tracked via the Micro-Task Board, and the core processing logic is handled by dedicated Python functions for clarity and reliability.

## 7. Configuration and Dependencies

### Configuration

*   **Agent Models**: Agents within this module (e.g., `DataAnalysisSpecialist_v2`, `DataAnalysisAgencyCoordinator_v1`) are configured to use the `DEFAULT_AGENT_MODEL` imported from `cie_core.config`. This suggests a centralized configuration for agent model selection.
*   **Firestore Collection**: The Micro-Task Board uses a Firestore collection named `micro_task_board_cda`. This is hardcoded in `tools/micro_task_board_tool.py`.
*   **Stopwords**: A basic list of English stopwords is defined directly within `lib/data_analysis_micro_agents.py`. For production environments, this might be externalized or replaced with a more robust library.

### Key Dependencies

*   **Google Cloud Firestore**: This is a critical external dependency for the Micro-Task Board (`tools/micro_task_board_tool.py`). The system relies on Firestore for persistent task storage and retrieval.
*   **`google-cloud-firestore`**: The Python client library for interacting with Firestore.
*   **`google-adk` (Agents Development Kit)**: Used for defining and managing agents (e.g., `Agent`, `FunctionTool`). This is evident from the imports in the agent files.
*   **`cie_core`**: While `decon/data-analysis` is a distinct module, it has a dependency on `cie_core` for shared configurations, specifically `cie_core.config.DEFAULT_AGENT_MODEL`. This indicates that `decon` might be part of a larger ecosystem where `cie_core` provides foundational elements.
*   **Standard Python Libraries**:
    *   `json`: Used for serializing and deserializing payloads for the Micro-Task Board.
    *   `re`: Used for regular expression-based text processing in sentence segmentation and keyword extraction.
    *   `uuid`: Used for generating unique IDs for Micro-Task Board entries.
    *   `datetime`: Used for handling timestamps.

The module is relatively self-contained within the `decon/data_analysis` path but relies on Firestore for its stateful operations and `cie_core` for some baseline configurations.
