#!/bin/bash
# deploy_cloud_run.sh 

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

# --- Define the tasks queue name ---
export TASKS_QUEUE_NAME="data-analysis-queue"

if [ -z "$PROJECT_ID" ] || [ -z "$SERVICE_NAME" ] || [ -z "$IMAGE_NAME" ]; then
    echo "ERROR: Required environment variables (PROJECT_ID, SERVICE_NAME, IMAGE_NAME) are not set."
    echo "Please run 'source gcenv.sh <IDENTIFIER>' before running this script."
    exit 1
fi

read -r -p "Proceed with deploying service '${SERVICE_NAME}'? (y/N): " confirmation
if ! [[ "$confirmation" =~ ^[Yy]$ ]];
then
    echo "Deployment cancelled by user."
    exit 0
fi

# --- Deployment Command ---
echo ""
echo "Deploying to Cloud Run..."

# We deploy an initial version without the SERVICE_URL to create the service.
echo "Initial deployment to establish service URL..."
gcloud run deploy "${SERVICE_NAME}" \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest" \
    --platform="managed" \
    --region="${REGION}" \
    --allow-unauthenticated \
    --project="${PROJECT_ID}" \
    --cpu=2 \
    --memory=4Gi

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${REGION}" --format "value(status.url)")

if [ -z "$SERVICE_URL" ]; then
    echo "ERROR: Could not retrieve Service URL. Halting deployment."
    exit 1
fi

echo "Service URL is: ${SERVICE_URL}"
echo "Redeploying to update service with all environment variables..."

# Final deployment with all environment variables correctly formatted
gcloud run deploy "${SERVICE_NAME}" \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest" \
    --platform="managed" \
    --region="${REGION}" \
    --allow-unauthenticated \
    --project="${PROJECT_ID}" \
    --cpu=2 \
    --memory=4Gi \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=TRUE,TASKS_QUEUE_NAME=${TASKS_QUEUE_NAME},SERVICE_URL=${SERVICE_URL}" \
    --set-secrets="CUSTOM_SEARCH_API_KEY=custom-search-api-key:latest,CUSTOM_SEARCH_ENGINE_ID=custom-search-engine-id:latest"

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