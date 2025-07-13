#!/bin/bash
# run_book_prep_build.sh

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u

# This script triggers the Cloud Build job to run the book preparation workflow.
# It assumes you have already sourced the correct gcenv.sh for your target environment.

# Check for required environment variables from gcenv.sh
if [ -z "${PROJECT_ID:-}" ] || [ -z "${LOCATION:-}" ] || [ -z "${GCS_BUCKET_NAME:-}" ] || [ -z "${GCS_FILE_NAME:-}" ]; then
    echo "ERROR: Required environment variables (PROJECT_ID, LOCATION, GCS_BUCKET_NAME, GCS_FILE_NAME) are not set."
    echo "Please run 'source gcenv.sh <IDENTIFIER>' before running this script."
    exit 1
fi

# --- Verification ---
echo ""
echo "--- Verifying Build Configuration from Sourced Environment ---"
echo "Project ID:   ${PROJECT_ID}"
echo "Location:     ${LOCATION}"
echo "Bucket Name:  ${GCS_BUCKET_NAME}"
echo "File Name:    ${GCS_FILE_NAME}"
echo "----------------------------------------------------------------"
echo ""

gcloud builds submit . \
    --config=cloudbuild.yaml \
    --project="${PROJECT_ID}" \
    --substitutions=_BUCKET_NAME="${GCS_BUCKET_NAME}",_FILE_NAME="${GCS_FILE_NAME}",_LOCATION="${LOCATION}"