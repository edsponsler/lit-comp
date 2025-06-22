# Project Name: Literary Companion

This project is a Python-based application designed to be deployed on Google Cloud Run. It utilizes Docker for containerization and a shell script for deployment.

## Prerequisites

- Google Cloud SDK installed and configured
- Docker installed
- Python 3.12

## Project Structure

- `app.py`: Main application file (Flask app).
- `Dockerfile`: Defines the Docker image for the application.
- `requirements.txt`: Lists Python dependencies.
- `deploy_cloud_run.sh`: Script for deploying the application to Google Cloud Run.
- `cie_core/`: Core application logic.
- `literary_companion/`: Sub-module for literary companion features.
- `templates/`: HTML templates for the Flask application.

## Build, Push, and Deploy

### 1. Set up Environment Variables

Before deploying, you need to set up environment variables. The `deploy_cloud_run.sh` script expects several variables to be set, including:

- `PROJECT_ID`: Your Google Cloud Project ID.
- `REGION`: The Google Cloud region for deployment (e.g., `us-central1`).
- `IMAGE_NAME`: The name for your Docker image.
- `SERVICE_NAME`: The name for your Cloud Run service.
- `REPO_NAME`: The name of your Artifact Registry repository.

It's recommended to create a `gcenv.sh` file (and add it to `.gitignore`) to manage these:

```bash
#!/bin/bash
# gcenv.sh - Environment variables for Google Cloud deployment

export PROJECT_ID="your-gcp-project-id"
export REGION="your-gcp-region" # e.g., us-central1
export IMAGE_NAME="your-image-name" # e.g., my-app-image
export SERVICE_NAME="your-service-name" # e.g., my-cloud-run-service
export REPO_NAME="your-artifact-registry-repo" # e.g., my-docker-repo

echo "Google Cloud environment variables set for ${PROJECT_ID}"
```

Source this file before running deployment scripts:
```bash
source gcenv.sh
```

### 2. Build the Docker Image

The `Dockerfile` specifies how to build the application image.

```bash
# Navigate to the project root directory
docker build -t "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest" .
```

**Explanation:**

- `docker build`: Command to build a Docker image.
- `-t "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"`: Tags the image with a name that includes your Google Cloud region, project ID, repository name, image name, and the `latest` tag. This format is required for pushing to Google Artifact Registry.
- `.`: Specifies that the build context (location of `Dockerfile` and application files) is the current directory.

### 3. Push the Docker Image to Artifact Registry

Once the image is built, push it to Google Artifact Registry (or your preferred container registry). Ensure you have authenticated Docker to access Artifact Registry.

```bash
# Authenticate Docker (if you haven't already for your region)
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Push the image
docker push "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
```

**Explanation:**
- `gcloud auth configure-docker ${REGION}-docker.pkg.dev`: Configures Docker to use `gcloud` credentials for pushing to Artifact Registry in the specified region.
- `docker push ...`: Pushes the tagged image to the specified Artifact Registry path.

### 4. Deploy to Google Cloud Run

The `deploy_cloud_run.sh` script handles the deployment to Cloud Run.

**Before running the script:**

1.  **Ensure Environment Variables are Set:** As mentioned in Step 1, source your `gcenv.sh` file.
    ```bash
    source gcenv.sh
    ```
2.  **Make the script executable:**
    ```bash
    chmod +x deploy_cloud_run.sh
    ```

**Run the deployment script:**

```bash
./deploy_cloud_run.sh
```

The script will:
1.  Verify that necessary environment variables (`PROJECT_ID`, `SERVICE_NAME`, `IMAGE_NAME`, `REGION`, `REPO_NAME`) are set.
2.  Prompt for confirmation before proceeding.
3.  Execute the `gcloud run deploy` command with appropriate parameters, including:
    *   Service name and image URL.
    *   Platform (managed) and region.
    *   Configuration for CPU, memory, and environment variables (like `GOOGLE_CLOUD_PROJECT`).
    *   Secrets configuration (e.g., `CUSTOM_SEARCH_API_KEY`).
    *   Allows unauthenticated invocations (adjust as needed for your security requirements).

The script will output the service URL upon successful deployment.

## Local Development

To run the Flask application locally for development:

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Set necessary environment variables.** At a minimum, `GOOGLE_CLOUD_PROJECT` might be needed if parts of your application interact with Google Cloud services even during local development. You might also need to set up local credentials for Google Cloud (e.g., via `gcloud auth application-default login`).
3.  **Run the Flask development server:**
    ```bash
    python app.py
    ```
    The application will typically be available at `http://127.0.0.1:5001` (as configured in `app.py`). For production, `gunicorn` is used as specified in the `Dockerfile`.

## Application Overview

The application consists of two main parts:

1.  **CIE Core (`cie_core/`)**:
    *   Provides a web interface (`/`) for users to submit queries.
    *   Uses a `coordinator_agent` to process these queries and generate reports.
    *   Interacts with Google Cloud services (e.g., Vertex AI, Firestore via `status_board_tool`).

2.  **Literary Companion (`literary_companion/`)**:
    *   Provides a web interface (`/literary_companion`) for literary-related functionalities.
    *   Features a `fun_fact_coordinator_v1` agent to generate fun facts based on text segments.
    *   Includes tools for interacting with Google Cloud Storage (`gcs_tool.py`) and other utilities.
    *   An API endpoint (`/api/get_novel_content`) proxies requests to fetch novel content from GCS.

Both modules leverage the Google ADK (Agent Development Kit) for building and running agents. The `app.py` file manages Flask routing, agent initialization, and asynchronous request handling.
