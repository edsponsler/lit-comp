# Collaborative Insight Engine (CIE) Core & Web UI Deployment

See also [Wiki](https://github.com/edsblog/cie-adk-tutorial/wiki)

Welcome to the Collaborative Insight Engine (CIE) project\! This README provides a comprehensive guide to understanding, setting up, building, and deploying the CIE. The CIE is a multi-agent system designed to automate the process of gathering, analyzing, and synthesizing information on a given topic to produce a concise report. This document will walk you through setting up the core CIE functionality and then deploying a web user interface for it on Google Cloud Run.

This project is useful for developers looking to explore multi-agent systems, automate research tasks, or build sophisticated information processing pipelines. By following this guide, you'll have a functional CIE system accessible via a web UI.

**Platform Requirements**

This tutorial assumes you are using the following development environment:

* **Operating System**: Windows with WSL 2 (Windows Subsystem for Linux 2)
* **Linux Distribution**: Ubuntu 24.04 LTS (running on WSL 2)
* **Python Version**: 3.12 (typically comes with Ubuntu 24.04)  
* **Development Environment**: Visual Studio Code with WSL integration  
* **Key Python Libraries**:  
  * google-adk==0.5.0  
  * google-cloud-firestore  
  * python-dotenv  
  * requests (for web requests)  
  * beautifulsoup4 (for HTML parsing)  
  * litellm (Optional but recommended by ADK setup)  
  * Flask\[async\] (for the web UI)  
  * gunicorn (for running Flask in Cloud Run)

All commands should generally be run in your WSL Ubuntu terminal unless specified otherwise. The primary working directory for this project will be ~/projects/cie-0.

## Part 0: Environment Setup and Foundations

This part establishes the groundwork for your CIE project.

### Step 0.1: Access Your WSL Ubuntu Environment

Open your WSL Ubuntu terminal.

### Step 0.2: Python Environment Setup

1. Confirm Python Version: Ubuntu 24.04 typically comes with Python 3.12. Verify with
```bash
python3 --version
```
2. Install Python venv and pip (if not already fully installed):  
```bash  
sudo apt update  
sudo apt install python3.12 python3.12-venv python3-pip
```
3. Create Project Directory:  
```bash  
mkdir -p ~/projects/cie-0  
cd ~/projects/cie-0
```
4. Create and Activate Virtual Environment:  
```bash  
python3 -m venv .venv  
source .venv/bin/activate  
```
Remember to activate the virtual environment every time you open a new terminal session for this project.

### Step 0.3: Install ADK and Essential Libraries

With the virtual environment active, install the necessary Python packages by creating a requirements.txt file (detailed in Web UI deployment, but good to install core ones now) or install them directly:

```bash
pip install google-adk==0.5.0  
pip install google-cloud-firestore python-dotenv requests beautifulsoup4  
pip install litellm # Optional but recommended by ADK
```
**Special Note**: We are specifying google-adk==0.5.0 as this is the version for which specific compatibility issues were resolved during the tutorial's development.

### Step 0.4: Google Cloud Project and Firestore Setup

1. Google Cloud Project: Ensure you have a Google Cloud Project (e.g., cie-0-123456).  
2. Enable APIs: In the Google Cloud Console for your project, enable:  
   * Cloud Firestore API  
   * Google Custom Search API  
   * Vertex AI API (usually aiplatform.googleapis.com)  
3. Create Firestore Database:  
   * Navigate to Firestore in the Google Cloud Console.  
   * Choose to create a database in **Native mode**.  
   * Select a location (e.g., us-central1).  
   * For security rules, start with **Test mode**.  
     * **Special Note on Security**: Remember to configure proper security rules for Firestore before deploying any application to production! Test mode allows open access for 30 days.

### Step 0.5: gcloud CLI Installation and Authentication

1. Install Snapd (if not present):  
```bash  
sudo apt update  
sudo apt install snapd
```
2. Install Google Cloud CLI:  
```bash  
sudo snap install google-cloud-cli --classic  
```
   Start a new WSL terminal session to ensure Snap paths are loaded correctly. 

3. Authenticate gcloud:  
```bash  
gcloud auth login
```
4. Set up Application Default Credentials (ADC):  
```bash  
gcloud auth application-default login  
```
   This allows your application to authenticate to Google Cloud services.

### Step 0.6: API Keys and Environment Variables

1. Google Custom Search API Key:  
   * Go to the Google Cloud Console -> APIs & Services -> Credentials.  
   * Create a new API key. Restrict this key to only allow the "Google Custom Search API".  
2. You'll also need a [Custom Search Engine ID](https://support.google.com/programmable-search/answer/12499034?hl=en) from the Programmable Search Engine control panel after creating a search engine.  
3. Open Project in VS Code:  
```bash  
cd ~/projects/cie-0  
code .
```
4. Create a .env file in the root of your cie-0 project directory:  
```bash
# For ADK to use Vertex AI models  
GOOGLE_GENAI_USE_VERTEXAI=TRUE  
GOOGLE_CLOUD_PROJECT=your-gcp-project-id # e.g., cie-0-123456  
GOOGLE_CLOUD_LOCATION=your-vertex-ai-region # e.g., us-central1

# For Search Service  
CUSTOM_SEARCH_API_KEY=PASTE_YOUR_SEARCH_API_KEY_HERE  
CUSTOM_SEARCH_ENGINE_ID=PASTE_YOUR_SEARCH_ENGINE_ID_HERE
```
5. Create a .gitignore file:
```bash 
# Virtual environment  
.venv/

# Environment variables  
.env

# Python cache  
__pycache__/  
*.pyc  
*.pyo  
*.pyd

# IDE and OS specific  
.vscode/  
.DS_Store  
```
**Special Note**: Always .gitignore your .venv directory and .env files.

### Step 0.7: Project File Structure

In your project's root directory (e.g., ~/projects/cie-0), create the agents and tools directories and initialize them as Python packages:

```bash
mkdir agents  
mkdir tools  
touch agents/__init__.py  
touch tools/__init__.py
```
### Step 0.8: Initialize Git Repository (Optional)

1. Initialize Git:  
```bash  
git init  
git add .  
git commit -m "Initial project setup for CIE Core"
```
2. Create a corresponding empty repository on your Git provider (e.g., GitHub).  
3. Link and push:  
```bash  
git remote add origin <your_remote_repository_ssh_or_https_url>  
git push -u origin main
```
### Step 0.9: Verify Firestore Setup

Create and run the Firestore Test Script [test_firestore.py](./test_firestore.py) in your project's root directory to confirm your connection.

```bash
python test_firestore.py
```
Confirm successful connection and data read/write. If you encounter errors, check the .env file for GOOGLE_CLOUD_PROJECT accuracy, API enablement, gcloud authentication, library installation, and Firestore database existence/rules.

## Part 1: Building Core CIE Components

This section covers the creation of the fundamental tools and specialist agents for the CIE.

### Step 1.1: Implement the Agent Status Board Tool

This tool allows agents to communicate and coordinate by reading from and writing to a shared "Agent Status Board" in Firestore.  

Create the Agent Status Board as [tools/status_board_tool.py](./tools/status_board_tool.py). This script creates two ADK FunctionTool instances: status_board_updater_tool is initialized with the update_status function and status_board_reader_tool is initialized with the get_status function. These functions update and get status messages from Firestore, along with a helper _make_serializable to handle datetime objects.

* **Special Note on Datetime Serialization**: Firestore Timestamp objects (or datetime.datetime) are not directly JSON serializable. They need conversion (e.g., to ISO 8601 string using .isoformat()) if they are part of a tool's return data that the ADK will process. The _make_serializable function handles this.  
* **Special Note on Optional Typing**: Use typing.Optional\[Type\] for optional arguments in functions wrapped by FunctionTool with google-adk==0.5.0 to avoid ADK parsing errors.

### Step 1.2: Implement the Web Scraping Search Tool

This tool uses the Google Custom Search API and scrapes basic content from web pages. Ensure requests and beautifulsoup4 are installed, and your API keys are in the .env file.  

Create the Web Scraping Search Tool as [tools/search_tools.py](./tools/search_tools.py). This script defines simple_web_search which queries the Google API, fetches pages, and uses BeautifulSoup to extract text from \<p\> tags, with error handling and content truncation. An ADK FuntionTool instance named search_tool is initialized with the simple_web_search function. 

### Step 1.3: Implement the Information Retrieval Specialist Agent

This agent uses the search_tool to find information and updates its status to the Agent Status Board using the status_board_updater_tool.  

Create the Information Retrieval Specialist Agent as [agents/information_retrieval_specialist.py](./agents/information_retrieval_specialist.py). Its prompt guides it to acknowledge tasks, use the search_tool, and report results (including output_references) or errors to the Agent Status Board, ensuring session_id and task_id are used correctly.

### Step 1.4: Implement the Data Analysis Specialist Agent

This agent processes data retrieved by the Information Retrieval Specialist Agent.  

Create the Data Analysis Specialist Agent as [agents/data_analysis_specialist.py](./agents/data_analysis_specialist.py). Its prompt instructs it to analyze provided text, extract insights, and update the Agent Status Board with structured findings in output_references.

### Step 1.5: Implement the Report Formatting Specialist Agent

This agent takes analyzed data and structures it into a final report.

Create the Report Formatting Specialist Agent as [agents/report_formatting_specialist.py](./agents/report_formatting_specialist.py). Its prompt details how to review analyzed data and formatting instructions, organize the information, write the report in Markdown, and update the Agent Status Board with the formatted report in output_references.

## Part 2: Testing and Refining the Information Retrieval Specialist

With the Web Scraping Search Tool and Information Retrieval Specialist Agent defined, test them together.

### Basic Interaction Test using the Retrieval Test Script

Create and use the Retrieval Test Script as [run_retrieval_test.py](./run_retrieval_test.py) to directly test the Information Retrieval Specialist Agent. This script sets up a runner, sends a query, iterates through agent events, and checks the Agent Status Board.

**Special Note on Content Length & Search Results**: Iterative testing with this script helps determine reliable settings for NUM_SEARCH_RESULTS and MAX_CONTENT_LENGTH in search_tools.py. A balance of NUM_SEARCH_RESULTS = 3 and MAX_CONTENT_LENGTH = 1500 characters was found to be stable. Remember that MAX_CONTENT_LENGTH is a character limit; 1500 characters is roughly 200-250 words.

## Part 3: Implementing and Refining the Coordinator Agent

The Coordinator Agent orchestrates the specialist agents.

### Implementing the Coordinator Agent

The Coordinator Agent uses specialist agents as tools via the AgentTool wrapper. 

Create the Coordinator Agent as [agents/coordinator_agent.py](./agents/coordinator_agent.py). This agent's prompt outlines a multi-phase plan: initial setup, information retrieval, data analysis, report formatting, and final delivery, detailing how to delegate tasks to specialists, pass session_id and sub-task task_ids, check their status using the status_board_reader_tool, and process their output_references.

* **Special Note on AgentTool Usage**: For google-adk==0.5.0, AgentTool is imported from google.adk.tools.agent_tool and instantiated with AgentTool(agent=specialist_agent_instance).  
* **Special Note on Explicit ID Passing**: For multi-agent coordination where sub-tasks need tracking, the orchestrating agent (Coordinator Agent) must be explicitly prompted to embed session_id and unique sub-task task_ids into the request string it sends to specialist agents. Specialists must then be prompted to use these exact IDs for their status updates.  
* **Special Note on get_status Loop / Conditional Logic**: Initially, the Coordinator Agent got stuck in a get_status loop which was resolved by restructuring its prompt. The new logic instructs the Coordinator to call get_status once ("Attempt 1") and explicitly examine the returned dictionary (checking results list, specialist's status field, and validity of output_references). If the task is completed and output is valid, it proceeds. If still processing, it makes only ONE MORE get_status call (see for example step P1_4b of the Coordinator Agent's instruction prompt). If not complete after the second check, it assumes an issue and proceeds, noting the problem. This "inspect and decide with bounded retry" logic is crucial.  
* **Special Note on ADK Instruction Templating**: Be cautious with literal curly braces {} in agent instruction strings, as the ADK might interpret them for variable substitution, potentially causing KeyError. Rephrasing or ensuring reliable escaping is necessary. F-strings in Python code constructing the prompt are safe.  
* **Special Note on Pydantic Validation**: The ADK uses Pydantic, and its ValidationError messages are very helpful for debugging tool and agent definitions.

## Part 4: Full System Test (CIE Coordinator Test)

Create [run_cie_coordinator_test.py](./run_cie_coordinator_test.py) to test the entire CIE Core workflow, orchestrated by the Coordinator Agent.

### Running the Full Pipeline

Run run_cie_coordinator_test.py in your project's root directory to test the full pipeline. This script initializes a session, sends a query to the Coordinator Agent, and logs events and the final report, followed by a Agent Status Board check. 

### Expected Outcome

When executed, you should observe:

* The Coordinator Agent initiates, creates a main task ID, and updates its status.  
* It delegates to specialists, passing correct session_id and sub-task task_ids.  
* Specialists use these IDs for their status updates and populate output_references.  
* The Coordinator Agent retrieves these outputs without endlessly looping.  
* This pattern repeats for all specialists.  
* A final report based on processed data is delivered.  
* The Agent Status Board shows distinct, correctly ID'd entries for all agents. This signifies a correctly functioning the CIE Core multi-agent system.

## Part 5: Deploying the CIE Web UI to Google Cloud Run

This section guides you through deploying a Flask-based web UI for the CIE Core to Google Cloud Run.

### Step 5.1: Web Application Setup (Flask)

1. Install Flask and Gunicorn:  
   Ensure your Python virtual environment is active and you are in ~/projects/cie-0.  
```bash  
pip install Flask[async] gunicorn
```
   * **Special Note on Flask\[async\]**: Flask\[async\] is required because the /process route in app.py is an async def function. Installing this prevents runtime errors.  
2. Update Project Structure for Web UI:  
   Create the following new files and directory within your project's root folder (e.g., ~/projects/cie-0):  
```plaintext
app.py
requirements.txt
Dockerfile
templates/index.html
```
3. Create requirements.txt:  
   Populate requirements.txt with all Python dependencies including the web-specific ones.  
```plaintext  
google-adk==0.5.0  
google-cloud-firestore  
python-dotenv  
requests  
beautifulsoup4  
litellm  
Flask[async]  
gunicorn
```
### Step 5.2: Building the User Interface

1. Create [templates/index.html](./templates/index.html): Populate templates/index.html with HTML, CSS, and JavaScript to create a form for user queries and a display area for the report.  
   * **Special Note on JavaScript**: The JavaScript in this file handles form submission, sends an asynchronous request to the /process backend endpoint, and displays the report or errors.

### Step 5.3: Backend Logic for CIE Integration (Flask app.py)

1. Create [app.py](./app.py): Populate app.py with the provided Flask application code. This script initializes Flask, serves index.html at the root route, and defines an async def process_query() route at /process to interact with the Coordinator Agent and return the report as JSON, including error handling.  
   * **Special Note on async def routes**: The async def route enables asynchronous operations with the ADK's Runner.run_async method.

### Step 5.4: Preparing for Deployment (Docker)

1. Create Dockerfile:  
   Create the Dockerfile.  
   * **Special Note on CMD instruction**: The CMD instruction in the Dockerfile must use the shell form (e.g., CMD exec gunicorn ...) or an entrypoint script for the $PORT environment variable to be correctly expanded. 

The array / exec form:
```bash
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "--timeout", "180", "app:app"]
```
might cause Gunicorn to see ${PORT} literally. 

Instead use:
```bash
CMD exec gunicorn --bind 0.0.0.0:$PORT --timeout 180 app:app
```

   * **Special Note on Gunicorn Timeout**: Gunicorn's default worker timeout (30 seconds) can be too short for the CIE's processing. Adding \--timeout 180 (or a suitable value) to the gunicorn command in the Dockerfile is crucial for longer-running queries.  
1. Create .dockerignore file:  
   Create the .dockerignore file to exclude unnecessary files (like .venv, \_\_pycache\_\_) from the Docker image, keeping it small and build times faster. For example [.dockerignore](./.dockerignore).

### Step 5.5: Deploying to Google Cloud Run

1. Enable Necessary Google Cloud APIs:  
   Ensure Cloud Run API, Artifact Registry API, Cloud Build API, Cloud Firestore API, Google Custom Search API, and Vertex AI API are enabled in your Google Cloud Project.  
2. Authenticate gcloud CLI:  
   Ensure gcloud is authenticated and ADC is set up:  
```bash  
gcloud auth login  
gcloud auth application-default login
```
   * **Special Note on ADC Quota Project**: The ADC setup must successfully associate with your project as a "quota project." This requires your user account to have the serviceusage.services.use permission (e.g., via the "Service Usage Consumer" role) on the project. Errors like USER_PROJECT_DENIED often stem from issues here.  
   * **Special Note on PROJECT_ID Accuracy**: A typo in PROJECT_ID can cause significant troubleshooting delays. Meticulously verify environment variables!  
3. Set Up Environment Variables for Deployment:  
   Use a script or set environment variables like PROJECT_ID, REGION, REPO_NAME, IMAGE_NAME. Example:  
```bash  
export PROJECT_ID="your-gcp-project-id"  
export REGION="your-vertex-ai-region" # e.g., us-central1  
export REPO_NAME="cie-repo"  
export IMAGE_NAME="cie-webapp"
```
4. Create a Docker Artifact Registry Repository:  
```bash  
gcloud artifacts repositories create ${REPO_NAME} \  
      --repository-format=docker \  
      --location=${REGION} \  
      --description="CIE Web Application Repository"
```
5. Configure Docker for Artifact Registry:  
   Authenticate Docker to your Artifact Registry:  
```bash  
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```
   * **Special Note on Docker CLI**: Ensure Docker CLI is installed and accessible in your WSL environment.  
6. Build and Tag the Docker Image:  
   Navigate to your project's root ~/projects/cie-0 and build the image:  
```bash  
docker build -t ${REGION}-docker.pkg.dev${PROJECT_ID}${REPO_NAME}${IMAGE_NAME}:latest .
```
   * **Special Note on Image Tagging**: If you change PROJECT_ID or other variables used in the tag, you must rebuild the image to apply the new tag before pushing; 'docker push' looks for an image with an exact matching local tag.  
7. Push the Docker Image:  
```bash  
docker push ${REGION}-docker.pkg.dev${PROJECT_ID}${REPO_NAME}${IMAGE_NAME}:latest
```
   * **Special Note on Permissions**: Ensure the user account pushing the image has the "Artifact Registry Writer" role (or equivalent) on the project.  
8. Deploy to Cloud Run:  
   Deploy using a command like the following, ensuring API keys are correctly substituted (preferably via a secure method, see "Important Considerations" below):  
```bash  
export SERVICE_NAME="cie-public-ui"  
gcloud run deploy "${SERVICE_NAME}" \  
      --image="${REGION}-docker.pkg.dev${PROJECT_ID}${REPO_NAME}${IMAGE_NAME}:latest" \  
      --platform="managed" \  
      --region="${REGION}" \  
      --allow-unauthenticated \  
      --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \  
      --set-env-vars="GOOGLE_CLOUD_LOCATION=${REGION}" \  
      --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE" \  
      --set-env-vars="CUSTOM_SEARCH_API_KEY=YOUR_ACTUAL_KEY" \  
      --set-env-vars="CUSTOM_SEARCH_ENGINE_ID=YOUR_ACTUAL_ID" \  
      --memory=2Gi \  
      --cpu=1 \  
      --project="${PROJECT_ID}"
```
You may wish to write a bash script like this [deploy_cloud_run.sh](./deploy_cloud_run.sh) to prompt for API keys. 
   * **Special Note on Cloud Run Resources**: Cloud Run services may need more than default memory (512MiB). Monitor logs for "out of memory" errors and adjust \--memory (e.g., 1Gi, 2Gi) and \--cpu.  
9. Assign IAM Roles to the Cloud Run Service Account:  
   * Once deployed, find the service account your Cloud Run service uses (in GCP Console under Cloud Run service details).  
   * Grant this service account these roles:  
     * "Cloud Datastore User" (for Firestore)  
     * "Vertex AI User" (for Vertex AI)

### Step 5.6: Testing the Deployed Application

Access the Service URL provided by Cloud Run after successful deployment. Enter a query and verify you receive a report.

* **Special Note on Logs & UI Errors**: Iterative testing and log analysis (Cloud Logging) are key. A UI error like "Unexpected token '\<'" often means a server-side 500 error where HTML (an error page) was returned instead of expected JSON.

## Important Considerations for Your Deployed Web UI

* **API Key Security**:  
  * Currently, API keys are passed as environment variables in the deployment command. This is insecure for production.  
  * **Recommendation**: Use Google Cloud Secret Manager to store secrets. Modify your Cloud Run deployment to securely access them. The Cloud Run service account will need the "Secret Manager Secret Accessor" role.  
* **Enhanced Error Handling**:  
  * The current Flask app has basic error handling.  
  * **Recommendation**: Implement more specific error catching, provide user-friendly UI messages, and log errors with more context.  
* **Managing Long-Running Processes**:  
  * CIE report generation can be lengthy. Synchronous HTTP handling isn't ideal for very long requests.  
  * **Recommendation**: For robust applications, use a task queue (like Google Cloud Tasks) for asynchronous report generation. The UI would submit a task and poll for results or use WebSockets/Server-Sent Events.  
* **Firestore Security Rules**:  
  * Your Firestore database was likely initialized in "Test mode" with open access.  
  * **Critical**: You **must** configure proper Firestore security rules to protect your data before production or wider use.  
* **ADK and Async - Gunicorn Workers**:  
  * app.py uses async def routes. Gunicorn runs with default synchronous workers.  
  * **Recommendation**: For higher concurrency with async Flask, consider an async Gunicorn worker class (e.g., uvicorn.workers.UvicornWorker). This requires adding uvicorn to requirements.txt and modifying the Gunicorn CMD in your Dockerfile.  
* **Cloud Run Service Configuration**:  
  * Adjust concurrency, min/max instances, and CPU allocation as needed.  
* **Cost Management**:  
  * Be mindful of costs for Cloud Run, Artifact Registry, Vertex AI, Custom Search API, and Firestore. Set up budget alerts.  
* **CI/CD (Continuous Integration/Continuous Deployment)**:  
  * For easier updates, consider a CI/CD pipeline using Cloud Build and a source repository.
