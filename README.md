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
