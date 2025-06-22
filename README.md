# CIE Web Application README

This document provides instructions for building, pushing, and deploying the CIE Web Application.

## Project Overview

The CIE Web Application is a Flask-based Python application that provides a web interface for users to submit queries and receive generated reports. It leverages Google Cloud services for deployment and functionality, including Cloud Run for serving the application and potentially other services like Vertex AI for report generation (as indicated by environment variables). The application uses a coordinator agent to process user queries and generate reports.

## Prerequisites

Before you begin, ensure you have the following tools installed and configured:

*   **Google Cloud SDK (gcloud CLI):** Required for interacting with Google Cloud services, including Artifact Registry and Cloud Run. Make sure it's initialized (`gcloud init`) and authenticated.
*   **Docker:** Required for building and running containerized applications.
*   **Python:** The application is written in Python (version 3.12 specified in Dockerfile). While the Docker container handles the Python environment for deployment, you might need Python installed locally for development or running scripts.
*   **`gcenv.sh` File:** This script, located in the project root (or as specified in `deploy_cloud_run.sh`), must be created and populated with your Google Cloud project details. It should define the following environment variables:
    *   `PROJECT_ID`: Your Google Cloud Project ID.
    *   `REGION`: The Google Cloud region for your resources (e.g., `us-central1`).
    *   `REPO_NAME`: The name of your Artifact Registry repository.
    *   `IMAGE_NAME`: The name for your Docker image.

    Example `gcenv.sh`:
    ```bash
    #!/bin/bash
    export PROJECT_ID="your-gcp-project-id"
    export REGION="your-gcp-region"
    export REPO_NAME="your-artifact-repo-name"
    export IMAGE_NAME="cie-web-app"
    ```
    **Note:** Ensure this file is executable (`chmod +x gcenv.sh`) and not committed to version control if it contains sensitive information, although these particular variables are generally not sensitive. The `deploy_cloud_run.sh` script sources this file.

## Build Instructions

The application is containerized using Docker. The `Dockerfile` in the project root defines the build process.

1.  **Navigate to the project root directory** where the `Dockerfile` is located.
2.  **Source your environment variables** (if you haven't already and if your `IMAGE_NAME` is used in the build command directly, though typically it's used for tagging before push):
    ```bash
    source gcenv.sh
    ```
3.  **Build the Docker image:**
    Replace `${REGION}`, `${PROJECT_ID}`, `${REPO_NAME}`, and `${IMAGE_NAME}` with the values from your `gcenv.sh` or your specific configuration. The tag `latest` is commonly used.
    ```bash
    docker build -t "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest" .
    ```
    *   The `Dockerfile` uses `python:3.12-slim` as the base image.
    *   It copies `requirements.txt` and installs the Python dependencies using `pip`.
    *   Then, it copies the rest of the application code into the `/app` directory in the container.
    *   The `.dockerignore` file is used to exclude unnecessary files (like `.git`, `.venv`, `__pycache__`) from being copied into the image, optimizing the build process and image size.

## Push Instructions

After building the Docker image, you need to push it to Google Artifact Registry. The `deploy_cloud_run.sh` script uses an image path like `${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest`.

1.  **Ensure Docker is configured to authenticate with Google Cloud Artifact Registry:**
    If you haven't done this before for your region, run:
    ```bash
    gcloud auth configure-docker ${REGION}-docker.pkg.dev
    ```
    This command configures Docker to use your `gcloud` credentials to authenticate with Artifact Registry in the specified region.

2.  **Source your environment variables** (if you haven't already):
    ```bash
    source gcenv.sh
    ```

3.  **Push the Docker image:**
    Use the same image name and tag you used during the build step.
    ```bash
    docker push "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
    ```
    This will upload your locally built image to your specified Artifact Registry repository, making it available for deployment to Cloud Run.

## Deploy Instructions

The `deploy_cloud_run.sh` script is provided to automate the deployment to Google Cloud Run.

1.  **Ensure the `deploy_cloud_run.sh` script is executable:**
    ```bash
    chmod +x deploy_cloud_run.sh
    ```
2.  **Run the deployment script:**
    ```bash
    ./deploy_cloud_run.sh
    ```
    The script will:
    *   Source environment variables from `gcenv.sh`.
    *   Prompt you to enter `CUSTOM_SEARCH_API_KEY` and `CUSTOM_SEARCH_ENGINE_ID`. These are required for the application's functionality. **Handle these keys securely.**
    *   Display the deployment configuration for verification.
    *   Ask for confirmation before proceeding.
    *   Execute the `gcloud run deploy` command with the necessary parameters, including:
        *   Service name (default: `cie-public-ui`)
        *   Image URL from Artifact Registry
        *   Platform (managed) and region
        *   Allowing unauthenticated invocations (for public access)
        *   Setting environment variables: `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `GOOGLE_GENAI_USE_VERTEXAI`, `CUSTOM_SEARCH_API_KEY`, `CUSTOM_SEARCH_ENGINE_ID`.
        *   Memory and CPU configurations.

    Upon successful execution, the script will output the service URL. It might take a few moments for the new revision to become fully available.

**Manual Deployment (Alternative):**

If you prefer to deploy manually or need to customize the deployment further, you can use the `gcloud run deploy` command directly. Refer to the `deploy_cloud_run.sh` script for the command structure and required parameters. You will need to set all environment variables manually, including the API keys.
For example:
```bash
# Source env vars first
source gcenv.sh

# Example manual deploy command (ensure API keys are handled securely)
# You will be prompted for API keys if not set as env vars for the command
gcloud run deploy cie-public-ui \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest" \
    --platform="managed" \
    --region="${REGION}" \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-env-vars="GOOGLE_CLOUD_LOCATION=${REGION}" \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE" \
    --set-env-vars="CUSTOM_SEARCH_API_KEY=YOUR_API_KEY" \
    --set-env-vars="CUSTOM_SEARCH_ENGINE_ID=YOUR_ENGINE_ID" \
    --memory="2Gi" \
    --cpu="1" \
    --project="${PROJECT_ID}"
```

## Running the Application Locally

For development and testing, you can run the Flask application directly on your local machine.

1.  **Ensure Python and pip are installed.**
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    Navigate to the project root directory (where `requirements.txt` is located) and run:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set required environment variables:**
    The application (`app.py`) uses `dotenv` to load environment variables from a `.env` file. Create a `.env` file in the project root with the necessary variables. At a minimum, you might need:
    ```
    GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
    # If using Google Custom Search locally:
    CUSTOM_SEARCH_API_KEY="your_custom_search_api_key"
    CUSTOM_SEARCH_ENGINE_ID="your_custom_search_engine_id"
    # GOOGLE_GENAI_USE_VERTEXAI is set to TRUE in app.py and Dockerfile,
    # ensure your local environment or ADC is set up for Vertex AI if needed.
    ```
    **Note:** Add `.env` to your `.gitignore` file to avoid committing secrets.

5.  **Run the application:**
    From the project root directory, execute:
    ```bash
    python app.py
    ```
    The `app.py` script will start the Flask development server. By default (as seen in the `if __name__ == '__main__':` block), it usually runs on `http://127.0.0.1:5001` in debug mode. Check the console output for the exact address.

    The application uses Gunicorn for production deployment (as specified in the `Dockerfile` `CMD` instruction), but `python app.py` is suitable for local development.
