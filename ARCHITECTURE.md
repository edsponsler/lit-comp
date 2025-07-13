# Literary Companion - Architectural Reference

## 1. Introduction

The Literary Companion is a feature designed to enhance the experience of reading classic novels. It provides readers with a "modern English" translation of the text displayed alongside the original, and offers contextually relevant "fun facts" about the content being read. This is achieved through two main processes: a one-time book preparation phase and an interactive fun fact generation system.

## 2. Overall Architecture

The Literary Companion module operates with two distinct workflows:

*   **Book Preparation (Batch Workflow):** This is a one-time process per novel. It involves reading the novel's text, segmenting it into paragraphs, generating a modern English translation for each paragraph, and storing this structured data (original + translation) in Google Cloud Storage (GCS) for later use by the interactive reading UI.
    *   Flow: `CLI Script -> BookPreparationCoordinator_v1 Agent -> book_processor_tool (from gcs_tool.py) -> translation_tool.py & GCS`

*   **Fun Fact Generation (Interactive Workflow):** This workflow is triggered as a user reads the prepared novel in the web UI. When the user requests fun facts for the current reading passage, the system generates several types of insights (e.g., historical context, character analysis).
    *   Flow: `Web UI (literary_companion.html) -> Flask API (/generate_fun_facts) -> FunFactCoordinator_v1 Agent -> fun_fact_orchestrator_tool -> fun_fact_generators.py & fun_fact_micro_task_board_tool.py -> Vertex AI & Firestore`

## 3. Core Components (`literary_companion/`)

The `literary_companion/` directory contains all the specialized Python modules developed for this feature.

### 3.1 Agents (`literary_companion/agents/`)

These agents are built using the Google ADK and serve as orchestrators for specific tasks within the Literary Companion. They primarily coordinate complex Python functions exposed as tools.

*   **`BookPreparationCoordinator_v1` (`book_preparation_coordinator_v1.py`):**
    *   **Role:** Manages the one-time processing and preparation of a novel.
    *   **Functionality:**
        *   Invoked by the `scripts/run_book_preparation.py` script.
        *   Its primary task is to call the `book_processor_tool` (from `literary_companion/tools/gcs_tool.py`).
        *   It passes the GCS bucket and file name of the novel to the tool.
        *   The agent itself is simple, acting as an entry point to the more complex `book_processor_tool` workflow.
    *   **Tools Used:** `book_processor_tool`.

*   **`FunFactCoordinator_v1` (`fun_fact_coordinator_v1.py`):**
    *   **Role:** Manages the real-time generation of fun facts based on a user's reading progress.
    *   **Functionality:**
        *   Invoked by the Flask application (`app.py`) when the `/generate_fun_facts` API endpoint is called.
        *   Receives a text segment (the portion of the novel read so far), a `session_id`, and an `agency_task_id`.
        *   Its sole responsibility is to call the `fun_fact_orchestrator_tool` (from `literary_companion/tools/fun_fact_orchestrator.py`), passing along the received arguments.
        *   Returns the JSON result from the `fun_fact_orchestrator_tool` back to the Flask app.
    *   **Tools Used:** `fun_fact_orchestrator_tool`.

### 3.2 Tools (`literary_companion/tools/`)

These tools provide specific functionalities used by the agents or other parts of the Literary Companion system.

*   **`gcs_tool.py`:**
    *   **Role:** Handles all interactions with Google Cloud Storage for reading and writing novel content.
    *   **Key Functions/Tools:**
        *   `read_text_from_gcs(bucket_name, file_name)`: Reads raw text from a GCS file. Used by `app.py` via the `/api/get_novel_content` endpoint to serve prepared novel JSON.
        *   `write_text_to_gcs(bucket_name, file_name, content)`: Writes text content to a GCS file. (Used internally by `process_and_translate_book`).
        *   `process_and_translate_book(bucket_name, file_name)` (exposed as `book_processor_tool`):
            *   Orchestrates the entire book preparation workflow.
            *   Reads the original novel text from GCS.
            *   Splits the text into paragraphs.
            *   For each paragraph, it calls `translation_tool.translate_text` to get the modern English version.
            *   Constructs a JSON object containing pairs of original and translated paragraphs.
            *   Writes this JSON object to a new file in GCS (e.g., `original_filename_prepared.json`).
            *   This is the tool used by `BookPreparationCoordinator_v1`.

*   **`translation_tool.py`:**
    *   **Role:** Provides text translation capability, specifically for converting classic literary language into modern, easily understandable English.
    *   **Key Functions/Tools:**
        *   `translate_text(text)`: Takes a string of text. Uses a generative AI model (Vertex AI, via `DEFAULT_AGENT_MODEL` from `literary_companion.config`) to perform a stylistic translation/rephrasing. It's not translating between different languages but rather modernizing the English style. Used by `process_and_translate_book`.

*   **`fun_fact_orchestrator.py`:**
    *   **Role:** Manages the entire multi-step process of generating a set of fun facts for a given text segment. This is a deterministic Python workflow, not an AI agent.
    *   **Key Functions/Tools:**
        *   `run_fun_fact_generation(text_segment, session_id, agency_task_id)` (exposed as `fun_fact_orchestrator_tool`):
            *   Defines a list of fun fact categories (e.g., "historical_context", "geographical_setting").
            *   For each category:
                *   It posts an initial "new_task" entry to the `fun_fact_micro_task_board` (using `fun_fact_micro_task_board_tool.post_micro_entry`).
                *   It calls the corresponding `analyze_<category>` function from `literary_companion/lib/fun_fact_generators.py`, passing the `text_segment`.
                *   It posts the result from the generator function as a "completed" task entry to the `fun_fact_micro_task_board`.
            *   After processing all categories, it retrieves all "completed" entries for the given `agency_task_id` from the micro-task board.
            *   Aggregates these results into a single JSON object where keys are fact categories and values are the generated facts.
            *   Returns this JSON object as a string.
            *   This is the tool used by `FunFactCoordinator_v1`.

*   **`fun_fact_micro_task_board_tool.py`:**
    *   **Role:** Provides functions to interact with a dedicated Firestore collection (`fun_fact_micro_task_board`) that acts as a status and results board for the individual generation tasks within the `fun_fact_orchestrator_tool`.
    *   **Key Functions:**
        *   `post_micro_entry(...)`: Writes or updates an entry on the board. Used by `fun_fact_orchestrator_tool` to log the start and completion of each fun fact generation sub-task (e.g., generating "historical_context").
        *   `get_micro_entries(...)`: Retrieves entries from the board, typically filtered by `agency_task_id` and `task_type` or `status`. Used by `fun_fact_orchestrator_tool` to collect all results before aggregation.
    *   This board serves a more fine-grained, internal purpose for the `fun_fact_orchestrator_tool`.

### 3.3 Libraries (`literary_companion/lib/`)

These are supporting Python libraries that contain core business logic.

*   **`fun_fact_generators.py`:**
    *   **Role:** Contains the actual logic for generating individual fun facts.
    *   **Functionality:**
        *   Provides a set of functions, each named `analyze_<category>(text)` (e.g., `analyze_historical_context`, `analyze_character_sentiments`).
        *   Each function takes the text segment as input.
        *   Constructs a specific prompt tailored to the fact category.
        *   Makes a direct call to a generative AI model (Vertex AI, using `DEFAULT_AGENT_MODEL`) with the prompt and text to generate the fun fact.
        *   Returns a dictionary containing the status and the generated fact text.
        *   These functions are called by the `fun_fact_orchestrator_tool`.

## 4. Web Application Integration

The Literary Companion feature is integrated into the main Flask web application (`app.py`) and has its own dedicated user interface.

*   **Flask Application (`app.py`) Integration:**
    *   **`/` route:** Redirects to the `/literary_companion` page.
    *   **`/literary_companion` route:** Serves the main HTML page for the feature (`templates/literary_companion/literary_companion.html`).
    *   **`/api/get_novel_content` endpoint (GET):**
        *   Called by the `literary_companion.html` frontend to fetch the prepared novel data.
        *   Uses `literary_companion.tools.gcs_tool.read_text_from_gcs()` to read the processed JSON file (containing original and modern translated paragraphs) from GCS.
        *   Returns the novel data as a JSON response.
    *   **`/generate_fun_facts` endpoint (POST):**
        *   Called by `literary_companion.html` when the user requests fun facts.
        *   Receives a JSON payload with `text_segment` (the portion of the novel read so far) and `session_id`.
        *   Invokes the `FunFactCoordinator_v1` agent via the ADK `Runner`.
        *   Passes the `text_segment`, `session_id`, and a newly generated `agency_task_id` to the agent.
        *   Returns the JSON response from the agent (which contains the aggregated fun facts) to the frontend.

*   **User Interface (`templates/literary_companion/literary_companion.html`):**
    *   **Structure:**
        *   Displays two main panes: one for the original novel text and one for the "dynamic content."
        *   The dynamic content pane initially shows the modern English translation of the novel.
        *   A "Show Fun Facts" button allows the user to toggle the dynamic content pane to display fun facts.
    *   **Functionality:**
        *   **Loading Novels:** On page load, it calls the `/api/get_novel_content` endpoint to fetch and display the original and translated paragraphs.
        *   **Synchronized Scrolling:** Implements synchronized scrolling between the original text pane and the modern translation pane. As the user scrolls the original text, the translation pane attempts to keep the corresponding paragraph in view. It uses an `IntersectionObserver` to track the currently visible paragraph in the original text.
        *   **Fun Fact Generation:**
            *   When the "Show Fun Facts" button is clicked:
                *   It identifies the `lastVisibleParagraphId` from the original text pane.
                *   It constructs the `text_segment` by concatenating all original paragraphs from the beginning up to and including the `lastVisibleParagraphId`.
                *   It calls the `/generate_fun_facts` backend endpoint with this `text_segment` and a unique `readingSessionId`.
                *   Displays the returned fun facts in the dynamic content pane, replacing the modern translation.
                *   The button text changes to "Show Modern English" to allow toggling back.
            *   **Caching:** Fun facts are cached locally in the browser (`funFactsCache` JavaScript variable, keyed by `lastVisibleParagraphId`) to avoid redundant API calls if the user requests facts for the same passage again.

## 5. Data Flow and Orchestration

This section details the step-by-step processes for the two main workflows.

### 5.1 Book Preparation Data Flow (Batch)

1.  **Initiation:** A developer or administrator runs the `scripts/run_book_preparation.py` script from the command line, providing GCS bucket and input novel file name (e.g., `python scripts/run_book_preparation.py --bucket my-bucket --file moby_dick.txt`).
2.  **Agent Invocation:** The script initializes the ADK Runner and invokes the `BookPreparationCoordinator_v1` agent with a prompt containing the bucket and file name.
3.  **Tool Call:** The `BookPreparationCoordinator_v1` agent, as per its instructions, calls the `book_processor_tool` (which is `literary_companion.tools.gcs_tool.process_and_translate_book`) with the provided bucket and file name.
4.  **Book Processing (`process_and_translate_book` tool):**
    *   **Read Original:** The tool reads the full text of the novel from `gs://<bucket_name>/<file_name>`.
    *   **Paragraph Segmentation:** The text is split into paragraph blocks based on double newline characters.
    *   **Translation Loop:** For each paragraph:
        *   The paragraph text is cleaned (extra newlines removed).
        *   `literary_companion.tools.translation_tool.translate_text()` is called with the cleaned paragraph. This function internally uses a Vertex AI generative model to produce a modern English version.
        *   If translation is successful, an object containing `paragraph_id`, `original_text`, and `translated_text` is created.
    *   **Aggregation:** All such paragraph objects are collected into a list under a top-level `paragraphs` key.
    *   **Write Prepared JSON:** The aggregated list is serialized to a JSON string. This JSON string is then written to a new file in GCS, typically named `<file_name_without_ext>_prepared.json` (e.g., `gs://<bucket_name>/moby_dick_prepared.json`).
5.  **Completion:** The `book_processor_tool` returns a success or error message to the `BookPreparationCoordinator_v1` agent, which then provides this as its final response. The `run_book_preparation.py` script prints this final response.

### 5.2 Fun Fact Generation Data Flow (Interactive)

1.  **User Action:** The user is reading a novel in `literary_companion.html` and scrolls to a certain point. The `lastVisibleParagraphId` is updated by the `IntersectionObserver`.
2.  **Request Fun Facts:** The user clicks the "Show Fun Facts" button.
3.  **Frontend Logic (`literary_companion.html` JavaScript):**
    *   Checks if fun facts for `lastVisibleParagraphId` are already in `funFactsCache`. If so, renders them and stops.
    *   Constructs `text_segment`: all original text from the beginning of the novel up to `lastVisibleParagraphId`.
    *   Generates a `readingSessionId`.
    *   Sends a POST request to `/generate_fun_facts` with a JSON body: `{ "text_segment": textSegment, "session_id": readingSessionId }`.
4.  **API Handling (`app.py`):**
    *   The `/generate_fun_facts` endpoint receives the request.
    *   It generates a unique `agency_task_id` for this specific request.
    *   It initializes an ADK `Runner` with the `FunFactCoordinator_v1` agent.
    *   It invokes the agent with a prompt containing the `text_segment`, `session_id` (which is the `readingSessionId` from frontend), and the new `agency_task_id`.
5.  **Agent Tool Call (`FunFactCoordinator_v1`):**
    *   The agent calls the `fun_fact_orchestrator_tool` (which is `literary_companion.tools.fun_fact_orchestrator.run_fun_fact_generation`), passing through `text_segment`, `session_id`, and `agency_task_id`.
6.  **Orchestration (`run_fun_fact_generation` tool):**
    *   **Define Tasks:** A predefined list of fun fact types is established (e.g., "historical_context", "geographical_setting").
    *   **Log New Tasks:** For each fact type, `fun_fact_micro_task_board_tool.post_micro_entry` is called to create a "new_task" record in the `fun_fact_micro_task_board` Firestore collection, associated with the `agency_task_id`. This record includes the `text_segment` as input.
    *   **Generate Facts Loop:** For each fact type:
        *   The corresponding `analyze_<fact_type>()` function from `literary_companion.lib.fun_fact_generators` is called with the `text_segment`.
        *   **Individual Fact Generation (`fun_fact_generators.analyze_*`):** The specific generator function forms a prompt, calls the Vertex AI generative model, and gets a fact string in return.
        *   `fun_fact_micro_task_board_tool.post_micro_entry` is called again to update/create a "completed" record in Firestore for that fact type, storing the generated fact in `output_payload`.
    *   **Aggregate Results:** After all fact types are processed, `fun_fact_micro_task_board_tool.get_micro_entries` is called to retrieve all "completed" task entries for the current `agency_task_id`.
    *   The results are compiled into a single JSON object (e.g., `{"historical_context": {"status": "success", "fact": "..."}}`).
    *   This JSON object is returned as a string.
7.  **Response to Frontend:**
    *   The `FunFactCoordinator_v1` agent returns the JSON string from the tool.
    *   `app.py` sends this JSON string as the HTTP response to the frontend.
8.  **Display Fun Facts (`literary_companion.html` JavaScript):**
    *   The frontend receives the JSON.
    *   The fun facts are cached in `funFactsCache[lastVisibleParagraphId]`.
    *   The dynamic content pane is cleared and repopulated with the fun facts, each displayed in a "card" format.
    *   The button text changes to "Show Modern English."

## 6. State Management

State within the Literary Companion module is managed in a few key ways, differing by workflow:

*   **Google Cloud Storage (GCS):**
    *   **Role:** Persistent storage for novel content.
    *   **Usage:**
        *   Stores the original raw text files of novels (e.g., `moby_dick.txt`).
        *   Stores the processed/prepared novel files (e.g., `moby_dick_prepared.json`). These JSON files contain the original text and modern translation, paragraph by paragraph, and are the primary source for the reading UI.
    *   This is the long-term storage for the "state" of the books themselves.

*   **Firestore (`fun_fact_micro_task_board` collection):**
    *   **Role:** Temporary, fine-grained task tracking and results storage specifically for the `fun_fact_orchestrator_tool`.
    *   **Usage:**
        *   When `run_fun_fact_generation` is executed, it logs "new_task" entries for each type of fun fact it intends to generate (historical, geographical, etc.) under a specific `agency_task_id`.
        *   As each fun fact is generated by `fun_fact_generators.py`, the corresponding entry in Firestore is updated to "completed" and includes the generated `output_payload`.
        *   The orchestrator then reads these "completed" entries to aggregate the final set of fun facts.
    *   **Nature:** This is more of a transient operational datastore for a single, complex tool execution rather than long-term state. Entries are primarily useful during the lifecycle of a single `/generate_fun_facts` API call.

*   **Client-Side (Browser) State (`literary_companion.html`):**
    *   **Role:** Manages UI state and caches data to improve user experience and reduce redundant API calls.
    *   **Usage:**
        *   `paragraphsData`: Stores the currently loaded novel's paragraph objects (original and translated text).
        *   `lastVisibleParagraphId`: Tracks the ID of the paragraph most recently scrolled into view in the original text pane.
        *   `funFactsCache`: A JavaScript object that caches the fun facts received from the API, keyed by `lastVisibleParagraphId`. This prevents re-fetching fun facts for the same text segment.
        *   `isShowingFunFacts`: Boolean flag to toggle the view in the dynamic pane between modern translation and fun facts.
        *   `readingSessionId`: A unique ID for the user's current reading session, passed to the backend.

## 7. Key Libraries and Technologies

The Literary Companion module leverages several key Python libraries and Google Cloud technologies:

*   **Google Agent Development Kit (google-adk):** Used for the `BookPreparationCoordinator_v1` and `FunFactCoordinator_v1` agents, enabling them to be invoked via the ADK Runner and to use ADK Tools (`FunctionTool`).
*   **Flask (Flask\[async]):** The main web framework used by `app.py` to serve the `literary_companion.html` page and provide the API endpoints (`/api/get_novel_content`, `/generate_fun_facts`).
*   **Google Cloud Vertex AI:** Directly used by `literary_companion.lib.fun_fact_generators.py` and `literary_companion.tools.translation_tool.py` to interact with generative AI models (specified by `DEFAULT_AGENT_MODEL` from `literary_companion.config`) for generating fun facts and modern English translations.
*   **Google Cloud Storage (GCS):** Used for storing original novel text files and the processed JSON files containing original and translated paragraphs. Accessed via `google-cloud-storage` library in `gcs_tool.py`.
*   **Google Cloud Firestore:** Used by `fun_fact_micro_task_board_tool.py` to implement the `fun_fact_micro_task_board` collection. This provides a basic task tracking and results storage mechanism for the `fun_fact_orchestrator_tool`. Accessed via `google-cloud-firestore` library.
*   **Python Standard Libraries:**
    *   `json`: For serializing and deserializing data (e.g., prepared novel content, fun facts).
    *   `re`: For regular expressions, used in `gcs_tool.py` to split novel text into paragraphs.
    *   `uuid`: For generating unique IDs (e.g., `agency_task_id` in `app.py`, entry IDs in `fun_fact_micro_task_board_tool.py`).
    *   `asyncio`: Used by `scripts/run_book_preparation.py` to run the ADK agent.
    *   `argparse`: Used by `scripts/run_book_preparation.py` to handle command-line arguments.
*   **No specific HTML/CSS/JS frameworks:** The `literary_companion.html` uses vanilla JavaScript, HTML, and CSS for its frontend logic and presentation.

## 8. Scripts

Associated scripts provide command-line interfaces for specific operations.

*   **`scripts/run_book_preparation.py`:**
    *   **Purpose:** To initiate the one-time batch processing of a novel.
    *   **Usage:**
        ```bash
        python scripts/run_book_preparation.py --bucket <your-gcs-bucket-name> --file <path-to-novel-in-bucket.txt>
        ```
    *   **Functionality:** Takes GCS bucket and file path as arguments. It then invokes the `BookPreparationCoordinator_v1` agent to process the specified novel. The agent, through the `book_processor_tool`, will read the novel, translate it paragraph by paragraph into modern English, and save the structured result (original + translation) as a JSON file back to the same GCS bucket with a `_prepared.json` suffix. This script is essential for making new novels available to the Literary Companion UI.
