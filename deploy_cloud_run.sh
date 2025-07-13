#!/bin/bash
# deploy_cloud_run.sh 

# This script ASSUMES you have already sourced the correct gcenv.sh for your target environment. 

# --- Verification ---
echo ""
echo "--- Verifying Deployment Configuration from Sourced Environment ---" 
echo "Project ID:             ${PROJECT_ID}"
echo "Location:               ${LOCATION}"
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
    --image="${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest" \
    --platform="managed" \
    --region="${LOCATION}" \
    --allow-unauthenticated \
    --project="${PROJECT_ID}" \
    --cpu=2 \
    --memory=2Gi \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-env-vars="GOOGLE_CLOUD_LOCATION=${LOCATION}" \
    --set-env-vars="GCS_BUCKET_NAME=${GCS_BUCKET_NAME}" \
    --set-env-vars="GCS_FILE_NAME=${GCS_FILE_NAME}" \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE" \
    --set-env-vars="DEFAULT_AGENT_MODEL=${DEFAULT_AGENT_MODEL}"

# Check deployment status
if [ $? -eq 0 ]; then 
    echo ""
    echo "Deployment command executed successfully for service [${SERVICE_NAME}]." 
    echo "Check the output above for the service URL and status."

    # --- Post-Deployment: Display Service Account for IAM Configuration ---
    SERVICE_ACCOUNT=$(gcloud run services describe "${SERVICE_NAME}" --platform="managed" --region="${LOCATION}" --project="${PROJECT_ID}" --format="value(spec.template.spec.serviceAccountName)")

    if [ -n "$SERVICE_ACCOUNT" ]; then
        echo ""
        echo "--- ACTION REQUIRED ---"
        echo "Ensure the Cloud Run service account has the necessary IAM roles."
        echo "Service Account: ${SERVICE_ACCOUNT}"
        echo "Required Roles:"
        echo "  - Vertex AI User (for GenAI calls)"
        echo "  - Cloud Datastore User (for Firestore access)"
        echo "  - Storage Object Admin (for GCS access)"
        echo "-----------------------"
    fi
else
    echo "" 
    echo "ERROR: Deployment command failed. Check the error messages above." 
    exit 1 
fi
exit 0