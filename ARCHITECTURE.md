# Architecture Document: Literary Companion

## 1. Introduction

This document provides a comprehensive overview of the architecture of the Literary Companion application. It details the various components, their interactions, the deployment workflow, and the specific Google Cloud services utilized. The application is designed to assist users in preparing literary works and generating screenplays, leveraging large language models (LLMs) and cloud-native services.

## 2. Overall Architecture

The Literary Companion application follows a modular and cloud-native architecture, primarily deployed on Google Cloud Platform (GCP). It consists of a core Flask web application, background processing scripts, and a suite of specialized agents and tools that interact with various GCP services, particularly for LLM-driven tasks and data storage.

```
+-------------------+     +---------------------+     +---------------------+
|                   |     |                     |     |                     |
|   User Interface  |<--->|  Flask Web App      |<--->|  Literary Agents    |
|   (Browser)       |     |    (app.py)         |     |  (Book Prep, Screenplay) |
|                   |     |                     |     |                     |
+-------------------+     +---------------------+     +---------------------+
                                   |       ^
                                   |       |
                                   v       |
+---------------------+     +---------------------+     +---------------------+
|                     |     |                     |     |                     |
|  Background Scripts |<--->|  Specialized Tools  |<--->|  Google Cloud Services |
|  (run_book_prep,    |     |  (GCS, Screenplay,  |     |  (Vertex AI, GCS,    |
|   run_screenplay)   |     |   Translation)      |     |   Firestore, Cloud Run) |
|                     |     |                     |     |                     |
+---------------------+     +---------------------+     +---------------------+
```

## 3. Core Application (`app.py`)

`app.py` serves as the main entry point for the web application. It is a Flask-based application responsible for:

*   **Serving the User Interface**: Renders HTML templates (from the `templates/` directory) to provide the user-facing interface.
*   **API Endpoints**: Exposes RESTful API endpoints for initiating workflows (e.g., book preparation, screenplay creation) and retrieving results.
*   **Orchestration**: Interacts with the `literary_companion/agents/` to delegate complex, LLM-driven tasks.
*   **Configuration**: Utilizes settings defined in `literary_companion/config.py`.

## 4. Deployment Workflow

The application is containerized using Docker and deployed to Google Cloud Run, enabling a serverless, scalable, and cost-effective deployment model.

*   **Dockerfile**: Defines the build process for the Docker image. It uses a multi-stage build to create a lean final image, installing Python dependencies into a virtual environment and copying only the necessary application code.
*   **.dockerignore**: Specifies files and directories to exclude from the Docker build context, ensuring a smaller and more secure image.
*   **requirements.txt**: Lists all Python dependencies required by the application.
*   **gcenv.sh.example / gcenv.sh**: A shell script template for managing environment variables (e.g., `PROJECT_ID`, `LOCATION`, `IMAGE_NAME`, `SERVICE_NAME`) specific to different deployment environments. This script is sourced before deployment.
*   **deploy_cloud_run.sh**: An automated script that orchestrates the deployment to Cloud Run. It performs the following steps:
    1.  Verifies that necessary environment variables are set.
    2.  Prompts for user confirmation before proceeding.
    3.  Deploys the Docker image to Google Cloud Run, configuring service parameters such as image URL, platform, region, authentication, CPU, memory, and environment variables.
    4.  Outputs the Cloud Run service account name, which is crucial for subsequent IAM role assignments.
*   **Google Cloud Run**: The serverless platform where the application runs. It automatically scales the application up and down based on traffic, including scaling to zero instances when idle.
*   **Artifact Registry**: Google Cloud's universal package manager, used here to store the Docker images built for the application. The `deploy_cloud_run.sh` script pushes the built image to a designated Docker repository within Artifact Registry.

## 5. Book Preparation Workflow

This workflow processes raw book files, preparing them for further analysis or use within the application.

*   **Trigger**: Initiated via `scripts/run_book_preparation.py`, which can be run as a background job or manually.
*   **Agent**: `literary_companion/agents/book_preparation_coordinator_v1.py`. This agent is responsible for:
    *   Receiving a raw book file (e.g., from GCS).
    *   Orchestrating the parsing, cleaning, and structuring of the book content.
    *   Potentially interacting with LLMs for tasks like summarization or entity extraction.
    *   Storing the processed book data.
*   **Tools Used**:
    *   `literary_companion/tools/gcs_tool.py`: Used for reading raw book files from a Google Cloud Storage bucket and writing the processed book data back to GCS.
*   **Output**: Structured, processed book data stored in Google Cloud Storage, ready for subsequent workflows.

## 6. Screenplay Creation Workflow

This workflow generates a screenplay based on provided input, likely leveraging the processed book data.

*   **Trigger**: Initiated via `scripts/run_screenplay_creation.py`, which can be run as a background job or manually.
*   **Agent**: `literary_companion/agents/screenplay_coordinator_v1.py`. This agent is responsible for:
    *   Taking input (e.g., processed book data, user prompts).
    *   Coordinating the generation of a screenplay, likely involving multiple LLM calls for character development, scene descriptions, dialogue, etc.
    *   Structuring the generated screenplay into a desired format.
*   **Tools Used**:
    *   `literary_companion/tools/screenplay_generator_tool.py`: A specialized tool that encapsulates the logic for interacting with LLMs to generate screenplay elements.
    *   `literary_companion/tools/gcs_tool.py`: Used for reading input data (e.g., processed book) from GCS and writing the final generated screenplay to GCS.
*   **Output**: A complete screenplay document stored in Google Cloud Storage.

## 7. Key Components and Tools

Beyond the core workflows, several shared components and tools facilitate the application's functionality:

*   **`literary_companion/lib/fun_fact_generators.py`**: Contains logic for generating "fun facts," likely by querying LLMs with specific prompts based on input text.
*   **`literary_companion/tools/translation_tool.py`**: Provides functionality for translating text, leveraging LLMs or dedicated translation APIs.
*   **`literary_companion/tools/gcs_tool.py`**: A utility module for interacting with Google Cloud Storage. It provides functions for uploading and downloading blobs (files) to and from specified GCS buckets. This tool is fundamental for handling large input files (books) and storing processed outputs (prepared books, screenplays).
*   **`literary_companion/config.py`**: A centralized configuration file that stores application-wide settings, such as Google Cloud project IDs, bucket names, and LLM model names. This promotes maintainability and allows for easy adjustment of parameters across different environments.

## 8. Caching Mechanism

The application leverages Google Cloud Storage (GCS) as a persistent caching mechanism for the outputs of long-running and computationally expensive processes, specifically the book preparation and screenplay creation workflows.

*   **Mechanism**: Before initiating a book preparation or screenplay generation task, the system first checks if a pre-computed or pre-processed version of the output already exists in a designated GCS bucket. This check is typically based on a unique identifier derived from the input (e.g., a hash of the book content or a combination of input parameters for screenplay generation).
*   **How it Works**:
    1.  When a request for book preparation or screenplay generation comes in, the relevant agent (e.g., `BookPreparationCoordinatorV1`) computes a unique key for the expected output.
    2.  It then uses `gcs_tool.py` to check if a blob with this key exists in the designated GCS cache bucket.
    3.  If the blob exists, the agent downloads the cached output directly from GCS and returns it, bypassing the entire processing pipeline.
    4.  If the blob does not exist, the agent proceeds with the full computation (e.g., LLM calls, data processing).
    5.  Once the computation is complete, the agent uploads the newly generated output to the GCS cache bucket using the computed key, making it available for future requests.

*   **Advantages Compared to Not Using a Cache**:
    *   **Reduced Computation Cost**: The most significant advantage is avoiding redundant execution of expensive LLM calls and complex data processing. This directly translates to lower operational costs, especially for services like Vertex AI which are billed per token or per request.
    *   **Faster Response Times**: For repeated requests or common inputs, the system can serve results almost instantaneously from the cache, dramatically improving user experience by reducing latency from minutes (for full processing) to seconds (for cache retrieval).
    *   **Improved Scalability and Throughput**: By offloading repeated computations to the cache, the system can handle a higher volume of requests without needing to scale up its compute resources (e.g., Cloud Run instances, LLM quotas) proportionally. This reduces contention for LLM APIs.
    *   **Enhanced Resilience and Reliability**: Cached results provide a fallback. If the underlying LLM service experiences an outage or the processing pipeline encounters an error, previously computed results can still be served from the cache, maintaining partial service availability.
    *   **Reduced API Quota Consumption**: For LLM services with rate limits or quotas, caching helps stay within those limits by minimizing the number of actual API calls.

## 9. Google Cloud Services Utilized

The Literary Companion application heavily relies on the following Google Cloud services:

*   **Cloud Run**: The primary serverless compute platform for hosting the Flask web application. It provides automatic scaling, traffic management, and integrates seamlessly with other GCP services.
*   **Artifact Registry**: Used for secure and private storage of Docker container images.
*   **Vertex AI**: Google Cloud's machine learning platform, specifically utilized for accessing Large Language Models (LLMs). This service powers the generative capabilities for tasks like fun fact generation, translation, book summarization, and screenplay creation.
*   **Cloud Storage (GCS)**: A highly scalable and durable object storage service. It serves multiple purposes:
    *   **Raw Input Storage**: Stores the original book files uploaded by users.
    *   **Processed Data Storage**: Stores the intermediate and final outputs of workflows, such as prepared book data and generated screenplays.
    *   **Caching Layer**: Acts as the persistent cache for computationally expensive results, as detailed in Section 8.
*   **Firestore (in Datastore mode)**: A NoSQL document database used for storing application metadata, user data, or potentially tracking the status of long-running tasks. The `deploy_cloud_run.sh` script explicitly requests the `Cloud Datastore User` IAM role, indicating its usage.