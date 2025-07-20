# Literary Companion AI

Welcome to the Literary Companion AI project! This is the initial phase of an ambitious three-phase project to build a sophisticated, RAG-based conversational AI agent designed to interact with and provide insights on a large corpus of domain-specific source material.

## Project Overview

The ultimate vision of this project is to create an AI-powered literary companion that can engage in deep, meaningful conversations about a vast collection of literary works. This will be achieved in three distinct phases:

*   **Phase 1: Data Ingestion and Indexing (Current Phase)**: The foundational phase of the project. Here, we focus on ingesting, processing, and indexing a large corpus of literary texts. The primary goal is to transform raw source material into a structured, enriched format that can be efficiently queried and utilized by a retrieval-augmented generation (RAG) model.
*   **Phase 2: RAG Implementation and Conversational AI Development**: In the second phase, we will build the core conversational AI agent. This will involve leveraging the indexed data from Phase 1 to develop a RAG-based system that can accurately retrieve relevant information and generate insightful, context-aware responses.
*   **Phase 3: Advanced Features and User Interface**: The final phase will focus on enhancing the user experience. This will include developing a user-friendly interface, integrating advanced features such as character analysis and thematic exploration, and refining the AI's conversational abilities.

## Architecture and Workflow

The current architecture is designed to support the data ingestion and indexing pipeline of Phase 1. The key components and workflow are as follows:

1.  **Source Material**: The process begins with a large corpus of literary texts, such as the included "Moby Dick" by Herman Melville.
2.  **Data Ingestion**: The `scripts/migrate_prepared_json.py` script is used to process the raw text. It cleans the text, splits it into paragraphs, and enriches it with metadata such as chapter and paragraph numbers.
3.  **Structured Data**: The output of the ingestion process is a structured JSON file (e.g., `pg2701-moby-dick-all_prepared_v2.json`), where each entry represents a paragraph with its associated metadata.
4.  **Cloud Storage**: The processed JSON files are stored in a Google Cloud Storage (GCS) bucket, making them easily accessible for future use in the RAG pipeline.

## Local Setup and Development

To get started with the project locally, follow these steps:

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd lit-comp
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Create a `gcenv.sh` file by copying the example:
    ```bash
    cp gcenv.sh.example gcenv.sh
    ```
    Edit `gcenv.sh` and replace the placeholder values with your Google Cloud project details. Then, source the file:
    ```bash
    source gcenv.sh your-identifier
    ```

5.  **Run the Ingestion Script**:
    You can now run the data ingestion script to process a book:
    ```bash
    python3 scripts/migrate_prepared_json.py scripts/assets/pg2701-moby-dick-all.txt scripts/assets/pg2701-moby-dick-all_prepared.json
    ```

## Contributing and Future Development

We welcome contributions to the Literary Companion AI project! Here are some areas where you can get involved:

*   **Testing**: The project currently lacks a dedicated testing suite. Introducing unit tests for the data ingestion scripts and other components would greatly improve code quality and reliability.
*   **Documentation**: Enhancing the documentation, both in the code and in the README, would make it easier for new contributors to get involved.
*   **New Feature Ideas**:
    *   **Character and Location Extraction**: Extend the data ingestion pipeline to identify and extract named entities such as characters and locations.
    *   **Thematic Analysis**: Develop tools to perform thematic analysis on the indexed texts.
    *   **Support for More Formats**: Add support for ingesting books in different formats, such as ePub or PDF.
*   **Refinement**:
    *   **Error Handling**: Improve the error handling in the data ingestion scripts to make them more robust.
    *   **Performance Optimization**: Optimize the performance of the data processing pipeline to handle larger corpora more efficiently.

We are excited to have you on board and look forward to your contributions!