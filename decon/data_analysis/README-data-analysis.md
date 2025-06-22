# Data Analysis Report Generation API

This project is a Flask-based web application that provides an API for generating data analysis reports. It utilizes Google Cloud services such as Cloud Run for deployment, Cloud Tasks for asynchronous task processing, and Vertex AI for generative AI capabilities. The application receives a user query, processes it asynchronously via Cloud Tasks, and then generates a report using AI agents.

## Core Functionality

*   **Web API:** Exposes endpoints to submit analysis queries (`/process`), check task status (`/status/<task_id>`), and an internal endpoint for task execution (`/run-task`).
*   **Asynchronous Processing:** Leverages Google Cloud Tasks to handle potentially long-running report generation processes without blocking the initial user request.
*   **AI-Powered Report Generation:** Uses a coordinator agent (`coordinator_agent`) which likely orchestrates other specialist agents to gather information and compile a report (details inferred from `app.py` and common patterns).
*   **Dockerized Deployment:** Packaged as a Docker container for consistent deployment environments, primarily targeting Google Cloud Run.

## Local Development (Conceptual)

While the primary deployment target is Google Cloud Run, for local development or testing, you would typically:

1.  **Set up Environment Variables:** Create a `.env` file based on the variables used in `app.py` and `deploy_cloud_run.sh` (e.g., `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `TASKS_QUEUE_NAME`, `CUSTOM_SEARCH_API_KEY`, `CUSTOM_SEARCH_ENGINE_ID`). For local testing, `SERVICE_URL` might point to `http://localhost:8080` or your ngrok URL if testing Cloud Task callbacks.
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Flask App:**
    ```bash
    python app.py
    ```
    The app will run on `http://localhost:5001` by default as per `app.py`'s `if __name__ == '__main__':` block. Note that the Dockerfile exposes and runs on port 8080.

    *Note: Full end-to-end testing locally would be complex due to the reliance on Google Cloud Tasks and IAM for the `/run-task` endpoint. You might need to mock these services or parts of the `process_query` and `run_task` functions.*

## Build, Push, and Deploy to Google Cloud Run

This section outlines the process for building the Docker image, pushing it to Google Artifact Registry, and deploying the application to Google Cloud Run.

### 1. Build Docker Image

The application is containerized using Docker. To build the Docker image:

a.  **Navigate to the project root directory** (where `Dockerfile` is located).

b.  **Run the build command:**
    Replace `your-image-name` with your desired image name (e.g., the value of `IMAGE_NAME` from `gcenv.sh`).
    ```bash
    docker build -t your-image-name .
    ```
    Example using `IMAGE_NAME` (e.g., `data-analysis-app`):
    ```bash
    docker build -t data-analysis-app .
    ```
    This command uses `Dockerfile` to copy the application code, install dependencies from `requirements.txt`, and package the application.

### 2. Push Docker Image to Artifact Registry

After building, push the image to Google Artifact Registry.

a.  **Authenticate Docker with Artifact Registry:**
    (If not already done) Configure Docker to authenticate with Artifact Registry in your target region. Replace `${REGION}` with your Google Cloud region (e.g., `us-central1`).
    ```bash
    gcloud auth configure-docker ${REGION}-docker.pkg.dev
    ```

b.  **Tag the Docker image:**
    Tag your local image with the Artifact Registry path. The format is `${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest`.
    *   `${REGION}`: Your Google Cloud region.
    *   `${PROJECT_ID}`: Your Google Cloud Project ID.
    *   `${REPO_NAME}`: Your Artifact Registry Docker repository name.
    *   `${IMAGE_NAME}`: Your image name.
    *   `your-local-image-name`: The name used in `docker build` (e.g., `data-analysis-app`).

    ```bash
    docker tag your-local-image-name ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest
    ```
    Example:
    ```bash
    docker tag data-analysis-app us-central1-docker.pkg.dev/my-gcp-project/my-docker-repo/data-analysis-app:latest
    ```

c.  **Push the Docker image:**
    ```bash
    docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest
    ```
    Example:
    ```bash
    docker push us-central1-docker.pkg.dev/my-gcp-project/my-docker-repo/data-analysis-app:latest
    ```

### 3. Deploy to Google Cloud Run

The `deploy_cloud_run.sh` script handles the deployment to Cloud Run.

**Prerequisites for Deployment:**

*   **Google Cloud SDK (`gcloud`):** Installed and authenticated.
*   **`gcenv.sh` File:** This environment configuration file must be present and sourced. It should define:
    *   `PROJECT_ID`
    *   `REGION`
    *   `IMAGE_NAME`
    *   `SERVICE_NAME`
    *   `REPO_NAME` (Artifact Registry repository name)
    *   Example `gcenv.sh`:
        ```bash
        #!/bin/bash
        export PROJECT_ID="your-gcp-project-id"
        export REGION="us-central1"
        export REPO_NAME="your-artifact-registry-repo-name" # e.g., 'docker-repo'
        export IMAGE_NAME="data-analysis-app"
        export SERVICE_NAME="data-analysis-service"
        ```
*   **Enabled APIs:** Cloud Run API, Artifact Registry API, Cloud Tasks API must be enabled in your GCP project.
*   **Cloud Tasks Invoker SA:** The service account `tasks-invoker-sa@${PROJECT_ID}.iam.gserviceaccount.com` (used in `app.py`) needs the `Cloud Run Invoker` role for the deployed service.
*   **Secrets Manager:** Secrets `custom-search-api-key` and `custom-search-engine-id` (referenced in `deploy_cloud_run.sh`) must exist in Secret Manager and be accessible by the Cloud Run service's runtime service account.

**Deployment Steps:**

a.  **Source Environment Configuration:**
    ```bash
    source gcenv.sh <IDENTIFIER>
    ```
    (Adjust `<IDENTIFIER>` if your `gcenv.sh` uses it for different environments, otherwise `source gcenv.sh` might suffice).

b.  **Run Deployment Script:**
    Ensure the latest Docker image is pushed (Step 2).
    ```bash
    ./deploy_cloud_run.sh
    ```
    The script will:
    *   Confirm environment variables.
    *   Deploy an initial service version to get the `SERVICE_URL`.
    *   Redeploy with all environment variables, including `SERVICE_URL` and secrets.
    *   Service configuration: 2 CPU, 4Gi Memory, Port 8080 (from Dockerfile).

    The script outputs the service URL upon successful deployment.

**Key Environment Variables for the Cloud Run Service (set by script):**
*   `GOOGLE_CLOUD_PROJECT=${PROJECT_ID}`
*   `GOOGLE_CLOUD_LOCATION=${REGION}`
*   `GOOGLE_GENAI_USE_VERTEXAI=TRUE`
*   `TASKS_QUEUE_NAME=data-analysis-queue`
*   `SERVICE_URL` (dynamically obtained service URL)
*   Secrets (mounted from Secret Manager):
    *   `CUSTOM_SEARCH_API_KEY`
    *   `CUSTOM_SEARCH_ENGINE_ID`

## Technologies Used

*   **Python 3.12**
*   **Flask:** Web framework.
*   **Gunicorn:** WSGI HTTP server.
*   **Docker:** Containerization.
*   **Google Cloud Run:** Serverless deployment platform.
*   **Google Cloud Tasks:** Asynchronous task management.
*   **Google Artifact Registry:** Docker image storage.
*   **Google Secret Manager:** Secure secret storage.
*   **Google Vertex AI (implied):** For generative AI capabilities via `google-genai` and `GOOGLE_GENAI_USE_VERTEXAI=TRUE`.
*   **`google-adk`:** (Assumed) Google Agent Development Kit for building AI agents.

## Project Structure Highlights

*   `app.py`: Main Flask application, defines API endpoints and task handling logic.
*   `Dockerfile`: Instructions to build the Docker image.
*   `requirements.txt`: Python dependencies.
*   `deploy_cloud_run.sh`: Shell script for deploying to Cloud Run.
*   `cie_core/`: Likely contains core components for the "Cognitive Information Extraction" engine, including agents.
    *   `cie_core/agents/coordinator_agent.py`: Central agent orchestrating the report generation.
*   `decon/data_analysis/`: Seems to be a module for "decomposed" data analysis, possibly containing more specialized agents or tools.
    *   `decon/data_analysis/tools/micro_task_board_tool.py`: Tool for managing sub-tasks or status updates.
*   `gcenv.sh` (Not included but required): Environment configuration script.

## Further Considerations / TODOs

*   **Testing:** Add details on how to run existing tests (`tests/`) and any specific configurations needed.
*   **API Usage Examples:** Provide `curl` or client code examples for interacting with the `/process` and `/status` endpoints.
*   **Detailed Configuration:** Explain any non-obvious configurations or assumptions made by the agents or tools.
*   **Error Handling and Monitoring:** Briefly mention how errors are handled and what monitoring/logging is in place or recommended.
*   **Contributing Guidelines:** If this is an open project, add a `CONTRIBUTING.md`.
*   **License:** Ensure `LICENSE` file is appropriate. The template included a mention of MIT license.
