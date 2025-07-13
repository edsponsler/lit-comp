#!/bin/bash
# gcenv.sh - Final Version

# Script to set Google Cloud environment variables for the CIE project
# This script now accepts an identifier to create unique names for services and images.
# Usage: source gcenv.sh <IDENTIFIER>
# Example: source gcenv.sh main
# Example: source gcenv.sh lit-comp

# --- USER CONFIGURATION (BASE NAMES) ---
GCP_PROJECT_ID="lit-comp-1171089"        # Your Google Cloud Project ID
GCP_LOCATION="us-central1"          # Your Google Cloud location/region
ARTIFACT_REPO_NAME="lit-comp-repo"           # Your Artifact Registry repository name
BASE_DOCKER_IMAGE_NAME="webapp"     # The base name for your Docker images
BASE_SERVICE_NAME="public-ui"       # The base name for your Cloud Run services
GCS_BUCKET_NAME="lit-comp-1171089-literary-companion-assets" # The GCS bucket for novel files
GCS_FILE_NAME="pg2701-moby-dick-all.txt" # The default GCS file to process
GCP_GENERATIVE_MODEL="gemini-2.5-flash" # The Vertex AI model for agents and tools

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
export GOOGLE_CLOUD_PROJECT="${GCP_PROJECT_ID}" # For ADK/Vertex and other libraries
export LOCATION="${GCP_LOCATION}"               # For gcloud commands (e.g., --region)
export GOOGLE_CLOUD_LOCATION="${GCP_LOCATION}"  # For Python client libraries
export REPO_NAME="${ARTIFACT_REPO_NAME}"
export IMAGE_NAME="${BASE_DOCKER_IMAGE_NAME}-${APP_IDENTIFIER}"
export SERVICE_NAME="${BASE_SERVICE_NAME}-${APP_IDENTIFIER}"
export GCS_BUCKET_NAME="${GCS_BUCKET_NAME}"
export GCS_FILE_NAME="${GCS_FILE_NAME}"
export DEFAULT_AGENT_MODEL="${GCP_GENERATIVE_MODEL}"

# --- THE FIX: Set the active gcloud project configuration ---
gcloud config set project "${PROJECT_ID}"

# --- THE FIX: Add the critical environment variable for Vertex AI mode ---
export GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Confirmation message
echo "Google Cloud environment variables set for '${APP_IDENTIFIER}':"
echo "PROJECT_ID: ${PROJECT_ID}"
echo "LOCATION:   ${LOCATION}"
echo "GOOGLE_CLOUD_LOCATION: ${GOOGLE_CLOUD_LOCATION}"
echo "REPO_NAME:    ${REPO_NAME}"
echo "IMAGE_NAME:   ${IMAGE_NAME}"
echo "SERVICE_NAME: ${SERVICE_NAME}"
echo "GCS_BUCKET_NAME: ${GCS_BUCKET_NAME}"
echo "GCS_FILE_NAME:   ${GCS_FILE_NAME}"
echo "DEFAULT_AGENT_MODEL: ${DEFAULT_AGENT_MODEL}"
echo "VERTEXAI_MODE:${GOOGLE_GENAI_USE_VERTEXAI}"