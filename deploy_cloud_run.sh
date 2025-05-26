#!/bin/bash

# Script to deploy the CIE Web Application to Google Cloud Run

# --- Configuration ---
# 1. Source environment variables for project, region, repo, and image names
#    This script assumes gcenv.sh is in the same directory or your project root.
#    Adjust the path if gcenv.sh is located elsewhere.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_SCRIPT_PATH="${SCRIPT_DIR}/gcenv.sh" # Assumes gcenv.sh is in the same directory

if [ -f "$ENV_SCRIPT_PATH" ]; then
    echo "Sourcing environment variables from $ENV_SCRIPT_PATH..."
    # shellcheck source=./gcenv.sh
    source "$ENV_SCRIPT_PATH"
else
    echo "ERROR: Environment script not found at $ENV_SCRIPT_PATH"
    echo "Please ensure gcenv.sh exists and contains your PROJECT_ID, REGION, REPO_NAME, and IMAGE_NAME."
    exit 1
fi

# 2. Define the Cloud Run service name
# You can change this if you prefer a different service name.
SERVICE_NAME="cie-public-ui"

# 3. API Keys - IMPORTANT: Handle these securely for production.
#    For this script, we'll prompt for them.
#    Alternatively, you can hardcode them here if you understand the risks,
#    or better yet, use Secret Manager for production deployments.

echo ""
echo "You will be prompted for your Google Custom Search API Key and Engine ID."
echo "These are required for the application to function."
echo ""

read -r -p "Enter your CUSTOM_SEARCH_API_KEY: " CUSTOM_SEARCH_API_KEY
read -r -p "Enter your CUSTOM_SEARCH_ENGINE_ID: " CUSTOM_SEARCH_ENGINE_ID

if [ -z "$CUSTOM_SEARCH_API_KEY" ] || [ -z "$CUSTOM_SEARCH_ENGINE_ID" ]; then
    echo "ERROR: Both Custom Search API Key and Engine ID are required."
    exit 1
fi

# --- Verification (Optional but Recommended) ---
echo ""
echo "--- Deployment Configuration ---"
echo "Project ID:             ${PROJECT_ID}"
echo "Region:                 ${REGION}"
echo "Artifact Repo Name:     ${REPO_NAME}"
echo "Docker Image Name:      ${IMAGE_NAME}"
echo "Cloud Run Service Name: ${SERVICE_NAME}"
echo "Image to Deploy:        ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
echo "------------------------------"
echo ""

read -r -p "Proceed with deployment? (y/N): " confirmation
if ! [[ "$confirmation" =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled by user."
    exit 0
fi

# --- Deployment Command ---
echo ""
echo "Deploying to Cloud Run..."

gcloud run deploy "${SERVICE_NAME}" \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest" \
    --platform="managed" \
    --region="${REGION}" \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-env-vars="GOOGLE_CLOUD_LOCATION=${REGION}" \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE" \
    --set-env-vars="CUSTOM_SEARCH_API_KEY=${CUSTOM_SEARCH_API_KEY}" \
    --set-env-vars="CUSTOM_SEARCH_ENGINE_ID=${CUSTOM_SEARCH_ENGINE_ID}" \
    --memory="2Gi" \
    --cpu="1" \
    --project="${PROJECT_ID}" # Explicitly set project for the gcloud command

# Check deployment status
if [ $? -eq 0 ]; then
    echo ""
    echo "Deployment command executed. Check the output above for the service URL and status."
    echo "It might take a few moments for the service to become fully available."
else
    echo ""
    echo "ERROR: Deployment command failed. Check the error messages above."
    exit 1
fi

exit 0
