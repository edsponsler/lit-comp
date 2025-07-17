# Deployment Guide: Literary Companion on Google Cloud Run

This guide provides step-by-step instructions for containerizing the Literary Companion Flask application with Docker and deploying it as a scalable, serverless service on Google Cloud Run.

## Prerequisites

Before you begin, ensure you have the following:

1.  **Google Cloud Project**: A GCP project with billing enabled.
2.  **gcloud CLI**: The [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated.
    ```bash
    gcloud auth login --no-browser
    gcloud auth application-default login --no-browser
    ```
3.  **Enabled APIs**: The following APIs enabled in your GCP project:
    *   Cloud Run API
    *   Artifact Registry API
    *   Cloud Build API
    *   Vertex AI API
    *   Cloud Firestore API
    *   Cloud Storage API
4.  **Docker**: [Docker](https://docs.docker.com/get-docker/) installed and running on your local machine.
5.  **Project Code**: You have the project source code on your local machine.

---

## Step 1: Configure Your Environment

The project uses a shell script, `gcenv.sh`, to manage environment variables for different deployment environments.

1.  **Source the script**: Open your terminal in the project root and run the following command. The `lit-comp` identifier is an example; you can use others like `dev` or `staging`.
    ```bash
    source gcenv.sh lit-comp
    ```
2.  **Verify**: The script will print the environment variables it has set, such as `PROJECT_ID`, `LOCATION`, `IMAGE_NAME`, and `SERVICE_NAME`. These will be used by subsequent scripts.

---

## Step 2: Create the Dockerfile

A `Dockerfile` is a text document that contains all the commands a user could call on the command line to assemble an image. The file you created earlier defines the steps to build a container image for our Python application.

---

## Step 3: Create the `.dockerignore` file

To keep your Docker image small and build times fast, a `.dockerignore` file excludes files and directories that are not needed in the final container. You have already created this file in the project root.

---

## Step 4: Set Up Google Artifact Registry

Artifact Registry is Google Cloud's service for storing and managing container images.

1.  **Create a Repository**: Run the following command, which uses the variables from `gcenv.sh`, to create a new Docker repository.
    ```bash
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${LOCATION}" \
        --description="Literary Companion Application Repository"
    ```

2.  **Configure Docker**: Authenticate the Docker CLI with your new repository.
    ```bash
    gcloud auth configure-docker "${LOCATION}-docker.pkg.dev"
    ```

---

## Step 5: Build and Push the Docker Image

Now, you will build the Docker image and push it to the Artifact Registry repository you just created.

1.  **Build the Image**: This command builds the image from your `Dockerfile` and tags it with the full path to your Artifact Registry repository.
    ```bash
    docker build -t "${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest" .
    ```

2.  **Push the Image**: This command uploads your tagged image to Artifact Registry.
    ```bash
    docker push "${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
    ```

---

## Step 6: Deploy to Google Cloud Run

The `deploy_cloud_run.sh` script automates the deployment process.

1.  **Run the Deployment Script**: Execute the script from your terminal.
    ```bash
    ./deploy_cloud_run.sh
    ```
2.  **Confirm**: The script will show you the configuration and ask for confirmation before proceeding. Type `y` and press Enter.

The script executes a `gcloud run deploy` command which tells Cloud Run to create a new service (or a new revision of an existing service) using the Docker image you just pushed. It also configures the service with the necessary environment variables.

---

## Step 7: Assign IAM Roles to the Service Account

After the first deployment, Cloud Run creates a dedicated service account for your service. This account acts as the identity of your application. By default, it has very few permissions. You must grant it the necessary roles to interact with other Google Cloud services like Vertex AI, Firestore, and Cloud Storage.

1.  **Find the Service Account Email**:
    *   **From the script output**: After a successful deployment, the `deploy_cloud_run.sh` script will now print the service account email directly to your terminal.
    *   **From the Google Cloud Console**: Navigate to the Cloud Run section, click on your service (e.g., `public-ui-lit-comp`), and go to the **Security** tab. The service account email will be listed there. It will look like `...@gcp-sa-run.iam.gserviceaccount.com`.

2.  **Grant Roles**:
    *   Navigate to the **IAM & Admin** page in the Google Cloud Console.
    *   Click the **Grant Access** button.
    *   In the "New principals" field, paste the service account email you found.
    *   In the "Assign roles" dropdown, find and add the following three roles:
        *   `Vertex AI User`: Allows the service to make calls to generative models for fun facts and translations.
        *   `Cloud Datastore User`: **(This is the one causing your error)**. Allows the service to read from and write to the Firestore database for the micro-task board.
        *   `Storage Object Admin`: Allows the service to read novel files from and write prepared files to Google Cloud Storage.
    *   Click **Save**.

It may take a minute or two for the new permissions to propagate. After that, your application should be able to write to Firestore without errors.

---

## Step 8: Test the Deployed Application

Once the deployment is complete and IAM roles are set, the `gcloud` command will output the URL for your service.

1.  **Access the URL**: Open the service URL in your web browser.
2.  **Test Functionality**: Interact with the application to ensure it can load the novel and generate fun facts.
3.  **Check Logs**: If you encounter any errors, you can view detailed logs for your service in the Google Cloud Console under "Cloud Run" -> (Your Service) -> "Logs".