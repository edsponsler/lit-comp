#!/bin/bash
# gcenv.sh - Final Version

# Script to set Google Cloud environment variables for the CIE project
# This script now accepts an identifier to create unique names for services and images.
# Usage: source gcenv.sh <IDENTIFIER>
# Example: source gcenv.sh main
# Example: source gcenv.sh lit-comp

# --- USER CONFIGURATION (BASE NAMES) ---
GCP_PROJECT_ID="cie-0-867530"        # Your Google Cloud Project ID
GCP_REGION="us-central1"          # Your Google Cloud region
ARTIFACT_REPO_NAME="cie-repo"           # Your Artifact Registry repository name
BASE_DOCKER_IMAGE_NAME="cie-webapp"     # The base name for your Docker images
BASE_SERVICE_NAME="cie-public-ui"       # The base name for your Cloud Run services

# --- SCRIPT LOGIC ---
# Check if an identifier was passed as an argument
if [ -z "$1" ]; then
    echo "ERROR: Please provide a unique identifier as an argument."
    echo "Usage: source gcenv.sh <IDENTIFIER>"
    return 1
fi

APP_IDENTIFIER="$1"

# Export the variables with the unique identifier appended
export PROJECT_ID="${GCP_PROJECT_ID}"
export GOOGLE_CLOUD_PROJECT="${GCP_PROJECT_ID}" # Also export this for ADK/Vertex
export REGION="${GCP_REGION}"
export GOOGLE_CLOUD_LOCATION="${GCP_REGION}"
export REPO_NAME="${ARTIFACT_REPO_NAME}"
export IMAGE_NAME="${BASE_DOCKER_IMAGE_NAME}-${APP_IDENTIFIER}"
export SERVICE_NAME="${BASE_SERVICE_NAME}-${APP_IDENTIFIER}"

# --- THE FIX: Add the critical environment variable for Vertex AI mode ---
export GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Confirmation message
echo "Google Cloud environment variables set for '${APP_IDENTIFIER}':"
echo "PROJECT_ID:   ${PROJECT_ID}"
echo "GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT}"
echo "REGION:       ${REGION}"
echo "GOOGLE_CLOUD_LOCATION: ${GOOGLE_CLOUD_LOCATION}"
echo "REPO_NAME:    ${REPO_NAME}"
echo "IMAGE_NAME:   ${IMAGE_NAME}"
echo "SERVICE_NAME: ${SERVICE_NAME}"
echo "VERTEXAI_MODE:${GOOGLE_GENAI_USE_VERTEXAI}"