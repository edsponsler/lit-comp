# Deployment Guide: Literary Companion on Google Cloud Run

This guide provides step-by-step instructions for containerizing the Literary Companion application with Docker and deploying it as a scalable, serverless service on Google Cloud Run.

## Prerequisites

Before you begin, ensure you have the following:

1.  **Google Cloud Project**: A GCP project with billing enabled.
2.  **gcloud CLI**: The [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated.
3.  **Enabled APIs**: The following APIs enabled in your GCP project:
    *   Cloud Run API
    *   Artifact Registry API
    *   Vertex AI API
    *   Cloud Firestore API
    *   Cloud Storage API
4.  **Docker**: [Docker](https://docs.docker.com/get-docker/) installed and running on your local machine.
5.  **Project Code**: You have the project source code on your local machine.

---

## Step 1: Configure Your Environment

The project uses a shell script, `gcenv.sh`, to manage environment variables for different deployment environments.

1.  **Create `gcenv.sh`**: Copy `gcenv.sh.example` to `gcenv.sh`.
2.  **Edit `gcenv.sh`**: Fill in the required values for your GCP project, location, and desired service names.
3.  **Source the script**: Open your terminal in the project root and run:
    ```bash
    source gcenv.sh
    ```
    This loads the necessary environment variables for the deployment scripts.

---

## Step 2: Build the Docker Image

The `Dockerfile` in the project root defines the container image for the application.

1.  **Build the Image**: Run the following command to build the image. It will be tagged with the name and location required for Artifact Registry, using the variables sourced from `gcenv.sh`.
    ```bash
    docker build -t "${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest" .
    ```

---

## Step 3: Push the Image to Artifact Registry

Artifact Registry is Google Cloud's service for storing and managing container images.

1.  **Create a Repository (if needed)**: If you haven't already, create a Docker repository in Artifact Registry.
    ```bash
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${LOCATION}" \
        --description="Literary Companion Application Repository"
    ```
2.  **Configure Docker**: Authenticate the Docker CLI with your repository.
    ```bash
    gcloud auth configure-docker "${LOCATION}-docker.pkg.dev"
    ```
3.  **Push the Image**: Upload your tagged image to Artifact Registry.
    ```bash
    docker push "${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
    ```

---

## Step 4: Deploy to Google Cloud Run

The `deploy_cloud_run.sh` script automates the deployment process.

1.  **Run the Deployment Script**:
    ```bash
    ./deploy_cloud_run.sh
    ```
2.  **Confirm**: The script will display the configuration and ask for confirmation. Type `y` and press Enter to proceed.

---

## Step 5: Assign IAM Roles to the Service Account

After the first deployment, Cloud Run creates a dedicated service account for your service. You must grant this account the necessary permissions to interact with other Google Cloud services.

1.  **Find the Service Account Email**: The `deploy_cloud_run.sh` script will print the service account email to your terminal after a successful deployment.

2.  **Grant Roles**: In the Google Cloud Console, navigate to the **IAM & Admin** page and grant the following roles to the service account email:
    *   `Vertex AI User`: Allows the service to make calls to generative models.
    *   `Cloud Datastore User`: Allows the service to read from and write to the Firestore database.
    *   `Storage Object Admin`: Allows the service to read and write files in Google Cloud Storage.

---

## Step 6: Test the Deployed Application

Once the deployment is complete and IAM roles are set, the `gcloud` command will output the URL for your service. Access this URL in your web browser to test the application. If you encounter errors, check the logs for your service in the Google Cloud Console.
