#!/bin/bash

# Script to deploy the CIE Web Application to Google Cloud Run
# This script ASSUMES you have already sourced the correct gcenv.sh for your target environment.

# --- Verification ---
echo ""
echo "--- Verifying Deployment Configuration from Sourced Environment ---"
echo "Project ID:             ${PROJECT_ID}"
echo "Region:                 ${REGION}"
echo "Docker Image Name:      ${IMAGE_NAME}"
echo "Cloud Run Service Name: ${SERVICE_NAME}"
echo "----------------------------------------------------------------"
echo ""

if [ -z "$PROJECT_ID" ] || [ -z "$SERVICE_NAME" ] || [ -z "$IMAGE_NAME" ]; then
    echo "ERROR: Required environment variables (PROJECT_ID, SERVICE_NAME, IMAGE_NAME) are not set."
    echo "Please run 'source gcenv.sh <IDENTIFIER>' before running this script."
    exit 1
fi

read -r -p "Proceed with deploying service '${SERVICE_NAME}'? (y/N): " confirmation
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
    --project="${PROJECT_ID}" \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-env-vars="GOOGLE_CLOUD_LOCATION=${REGION}" \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE" \
    --set-secrets="CUSTOM_SEARCH_API_KEY=custom-search-api-key:latest" \
    --set-secrets="CUSTOM_SEARCH_ENGINE_ID=custom-search-engine-id:latest"

# Check deployment status
if [ $? -eq 0 ]; then
    echo ""
    echo "Deployment command executed successfully for service [${SERVICE_NAME}]."
    echo "Check the output above for the service URL and status."
else
    echo ""
    echo "ERROR: Deployment command failed. Check the error messages above."
    exit 1
fi

exit 0