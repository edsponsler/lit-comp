# **Collaborative Insight Engine (CIE) Core & Web UI Deployment**

Welcome to the Collaborative Insight Engine (CIE) project\! This README provides a comprehensive guide to understanding, setting up, building, and deploying the CIE. The CIE is a multi-agent system designed to automate the process of gathering, analyzing, and synthesizing information on a given topic to produce a concise report. This document will walk you through setting up the core CIE functionality and then deploying a web user interface for it on Google Cloud Run.

This project is useful for developers looking to explore multi-agent systems, automate research tasks, or build sophisticated information processing pipelines. By following this guide, you'll have a functional CIE system accessible via a web UI.

## ---

**Platform Requirements**

This tutorial assumes you are using the following development environment:

* **Operating System**: Windows with WSL 2 (Windows Subsystem for Linux 2\)  
* **Linux Distribution**: Ubuntu 24.04 LTS (running on WSL 2\)  
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

All commands should generally be run in your WSL Ubuntu terminal unless specified otherwise. The primary working directory for this project will be \~/projects/cie-0.

## ---

**Part 0: Environment Setup and Foundations**

This part establishes the groundwork for your CIE project.

### **Step 0.1: Access Your WSL Ubuntu Environment**

Open your WSL Ubuntu terminal.

### **Step 0.2: Python Environment Setup**

1. **Confirm Python Version**: Ubuntu 24.04 typically comes with Python 3.12. Verify with python3 \--version.  
2. **Install Python venv and pip** (if not already fully installed):  
   Bash  
   sudo apt update  
   sudo apt install python3.12 python3.12-venv python3-pip

3. **Create Project Directory**:  
   Bash  
   mkdir \-p \~/projects/cie-0  
   cd \~/projects/cie-0

4. **Create and Activate Virtual Environment**:  
   Bash  
   python3 \-m venv .venv  
   source .venv/bin/activate  
   Remember to activate the virtual environment every time you open a new terminal session for this project.

### **Step 0.3: Install ADK and Essential Libraries**

With the virtual environment active, install the necessary Python packages by creating a requirements.txt file (detailed in Web UI deployment, but good to install core ones now) or install them directly:

Bash

pip install google-adk==0.5.0  
pip install google-cloud-firestore python-dotenv requests beautifulsoup4  
pip install litellm \# Optional but recommended by ADK

**Special Note**: We are specifying google-adk==0.5.0 as this is the version for which specific compatibility issues were resolved during the tutorial's development.

### **Step 0.4: Google Cloud Project and Firestore Setup**

1. **Google Cloud Project**: Ensure you have a Google Cloud Project (e.g., cie-0-867530).  
2. **Enable APIs**: In the Google Cloud Console for your project, enable:  
   * Cloud Firestore API  
   * Google Custom Search API  
   * Vertex AI API (usually aiplatform.googleapis.com)  
3. **Create Firestore Database**:  
   * Navigate to Firestore in the Google Cloud Console.  
   * Choose to create a database in **Native mode**.  
   * Select a **location** (e.g., us-central1).  
   * For **security rules**, start with **Test mode**.  
     * **Special Note on Security**: Remember to configure proper security rules for Firestore before deploying any application to production\! Test mode allows open access for 30 days.

### **Step 0.5: gcloud CLI Installation and Authentication**

1. **Install Snapd** (if not present):  
   Bash  
   sudo apt update  
   sudo apt install snapd

2. **Install Google Cloud CLI**:  
   Bash  
   sudo snap install google-cloud-cli \--classic  
   Start a new WSL terminal session to ensure Snap paths are loaded correctly.  
3. **Authenticate gcloud**:  
   Bash  
   gcloud auth login

4. **Set up Application Default Credentials (ADC)**:  
   Bash  
   gcloud auth application-default login  
   This allows your application to authenticate to Google Cloud services.

### **Step 0.6: API Keys and Environment Variables**

1. **Google Custom Search API Key**:  
   * Go to the Google Cloud Console \-\> APIs & Services \-\> Credentials.  
   * Create a new API key. Restrict this key to only allow the "Google Custom Search API".  
2. You'll also need a **Custom Search Engine ID** from the Programmable Search Engine control panel after creating a search engine.  
3. **Open Project in VS Code**:  
   Bash  
   cd \~/projects/cie-0  
   code .

4. Create a [.env file](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/.env%5D\(https://github.com/edsblog/cie-0/blob/main/.env\)) in the root of your cie-0 project directory:  
   Ini, TOML  
   \# For ADK to use Vertex AI models  
   GOOGLE\_GENAI\_USE\_VERTEXAI\=TRUE  
   GOOGLE\_CLOUD\_PROJECT\=your-gcp-project-id \# e.g., cie-0-867530  
   GOOGLE\_CLOUD\_LOCATION\=your-vertex-ai-region \# e.g., us-central1

   \# For Search Service  
   CUSTOM\_SEARCH\_API\_KEY\=PASTE\_YOUR\_SEARCH\_API\_KEY\_HERE  
   CUSTOM\_SEARCH\_ENGINE\_ID\=PASTE\_YOUR\_SEARCH\_ENGINE\_ID\_HERE

5. Create a [.gitignore file](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/.gitignore%5D\(https://github.com/edsblog/cie-0/blob/main/.gitignore\)):  
   \# Virtual environment  
   .venv/

   \# Environment variables  
   .env

   \# Python cache  
   \_\_pycache\_\_/  
   \*.pyc  
   \*.pyo  
   \*.pyd

   \# IDE and OS specific  
   .vscode/  
   .DS\_Store  
   **Special Note**: Always .gitignore your .venv directory and .env files.

### **Step 0.7: Project File Structure**

In your \~/projects/cie-0 directory, create the agents and tools directories and initialize them as Python packages:

Bash

mkdir agents  
mkdir tools  
touch agents/\_\_init\_\_.py  
touch tools/\_\_init\_\_.py

### **Step 0.8: Initialize Git Repository (Optional)**

1. **Initialize Git**:  
   Bash  
   git init  
   git add .  
   git commit \-m "Initial project setup for CIE Core"

2. Create a corresponding empty repository on your Git provider (e.g., GitHub).  
3. **Link and push**:  
   Bash  
   git remote add origin \<your\_remote\_repository\_ssh\_or\_https\_url\>  
   git push \-u origin main

### **Step 0.9: Verify Firestore Setup**

Create and run the [Firestore Test Script (test\_firestore.py)](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/test_firestore.py%5D\(https://github.com/edsblog/cie-0/blob/main/test_firestore.py\)) to confirm your connection.

Bash

python test\_firestore.py

Confirm successful connection and data read/write. If you encounter errors, check the .env file for GOOGLE\_CLOUD\_PROJECT accuracy, API enablement, gcloud authentication, library installation, and Firestore database existence/rules.

## ---

**Part 1: Building Core CIE Components**

This section covers the creation of the fundamental tools and specialist agents for the CIE.

### **Step 1.1: Implement the StatusBoardTool**

This tool allows agents to communicate and coordinate by reading from and writing to a shared "Agent Status Board" in Firestore.  
Create the StatusBoardTool (tools/status\_board\_tool.py). This script includes functions to update\_status and get\_status from Firestore, along with a helper \_make\_serializable to handle datetime objects.

* **Special Note on Datetime Serialization**: Firestore Timestamp objects (or datetime.datetime) are not directly JSON serializable. They need conversion (e.g., to ISO 8601 string using .isoformat()) if they are part of a tool's return data that the ADK will process. The \_make\_serializable function handles this.  
* **Special Note on Optional Typing**: Use typing.Optional\[Type\] for optional arguments in functions wrapped by FunctionTool with google-adk==0.5.0 to avoid ADK parsing errors.

### **Step 1.2: Implement the Real Search Tool with Web Scraping**

This tool uses the Google Custom Search API and scrapes basic content from web pages. Ensure requests and beautifulsoup4 are installed, and your API keys are in the .env file.  
Create/Update the Search Tool (tools/search\_tools.py). This script defines simple\_web\_search which queries the Google API, fetches pages, and uses BeautifulSoup to extract text from \<p\> tags, with error handling and content truncation.

### **Step 1.3: Implement the InformationRetrievalSpecialist Agent**

This agent uses the search\_tool to find information and updates its status using the status\_board\_updater\_tool.  
Create/Update the InformationRetrievalSpecialist Agent (agents/information\_retrieval\_specialist.py). Its prompt guides it to acknowledge tasks, use the search tool, and report results (including output\_references) or errors to the status board, ensuring session\_id and task\_id are used correctly.

### **Step 1.4: Implement the DataAnalysisSpecialist Agent**

This agent processes data retrieved by the InformationRetrievalSpecialist.  
Create the DataAnalysisSpecialist Agent (agents/data\_analysis\_specialist.py). Its prompt instructs it to analyze provided text, extract insights, and update the status board with structured findings in output\_references.

### **Step 1.5: Implement the ReportFormattingSpecialist Agent**

This agent takes analyzed data and structures it into a final report.  
Create the ReportFormattingSpecialist Agent (agents/report\_formatting\_specialist.py). Its prompt details how to review analyzed data and formatting instructions, organize the information, write the report (typically in Markdown), and update the status board with the formatted report in output\_references.

## ---

**Part 2: Testing and Refining the InformationRetrievalSpecialist**

With the real search tool and InformationRetrievalSpecialist defined, test them together.

### **Basic Interaction Test**

Use the [Retrieval Test Script (run\_retrieval\_test.py)](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/run_retrieval_test.py%5D\(https://github.com/edsblog/cie-0/blob/main/run_retrieval_test.py\)) to directly test the InformationRetrievalSpecialist. This script sets up a runner, sends a query, iterates through agent events, and checks the status board.

* **Special Note on Content Length & Search Results**: Iterative testing with this script helps determine reliable settings for NUM\_SEARCH\_RESULTS and MAX\_CONTENT\_LENGTH in search\_tools.py. A balance of NUM\_SEARCH\_RESULTS \= 3 and MAX\_CONTENT\_LENGTH \= 1500 characters was found to be stable. Remember that MAX\_CONTENT\_LENGTH is a character limit; 1500 characters is roughly 200-250 words.

## ---

**Part 3: Implementing and Refining the CoordinatorAgent**

The CoordinatorAgent orchestrates the specialist agents.

### **Implementing the CoordinatorAgent**

The CoordinatorAgent uses specialist agents as tools via the AgentTool wrapper.  
Create/Update the CoordinatorAgent (agents/coordinator\_agent.py). This agent's prompt outlines a multi-phase plan: initial setup, information retrieval, data analysis, report formatting, and final delivery, detailing how to delegate tasks to specialists, pass session\_id and sub-task task\_ids, check their status using the status\_board\_reader\_tool, and process their output\_references.

* **Special Note on AgentTool Usage**: For google-adk==0.5.0, AgentTool is imported from google.adk.tools.agent\_tool and instantiated with AgentTool(agent=specialist\_agent\_instance).  
* **Special Note on Explicit ID Passing**: For multi-agent coordination where sub-tasks need tracking, the orchestrating agent (Coordinator) must be explicitly prompted to embed session\_id and unique sub-task task\_ids into the request string it sends to specialist agents. Specialists must then be prompted to use these exact IDs for their status updates.  
* **Special Note on get\_status Loop / Conditional Logic**: The CoordinatorAgent's initial problem of getting stuck in a get\_status loop was resolved by restructuring its prompt. The new logic instructs the Coordinator to call get\_status once ("Attempt 1"), explicitly examine the returned dictionary (checking results list, specialist's status field, and validity of output\_references). If the task is completed and output is valid, it proceeds. If still processing, it makes only ONE MORE get\_status call ("Attempt 2"). If not complete after the second check, it assumes an issue and proceeds, noting the problem. This "inspect and decide with bounded retry" logic is crucial.  
* **Special Note on ADK Instruction Templating**: Be cautious with literal curly braces {} in agent instruction strings, as the ADK might interpret them for variable substitution, potentially causing KeyError. Rephrasing or ensuring reliable escaping is necessary. F-strings in Python code constructing the prompt are safe.  
* **Special Note on Pydantic Validation**: The ADK uses Pydantic, and its ValidationError messages are very helpful for debugging tool and agent definitions.

## ---

**Part 4: Full System Test (CIE Core)**

This script tests the entire CIE workflow, orchestrated by the CoordinatorAgent.

### **Running the Full Pipeline**

Use the [Coordinator Test Script (run\_coordinator\_level\_1\_test.py)](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/run_coordinator_level_1_test.py%5D\(https://github.com/edsblog/cie-0/blob/main/run_coordinator_level_1_test.py\)) to test the full pipeline. This script initializes a session, sends a query to the CoordinatorAgent, and logs events and the final report, followed by a status board check.

### **Expected Outcome**

When executed, you should observe:

* The CoordinatorAgent initiates, creates a main task ID, and updates its status.  
* It delegates to specialists, passing correct session\_id and sub-task task\_ids.  
* Specialists use these IDs for their status updates and populate output\_references.  
* The CoordinatorAgent retrieves these outputs without looping.  
* This pattern repeats for all specialists.  
* A final report based on processed data is delivered.  
* The status board shows distinct, correctly ID'd entries for all agents. This signifies a correctly functioning core CIE multi-agent system.

## ---

**Part 5: Deploying the CIE Web UI to Google Cloud Run**

This section guides you through deploying a Flask-based web UI for your CIE to Google Cloud Run.

### **Step 5.1: Web Application Setup (Flask)**

1. Install Flask and Gunicorn:  
   Ensure your Python virtual environment is active and you are in \~/projects/cie-0.  
   Bash  
   pip install Flask\[async\] gunicorn

   * **Special Note on Flask\[async\]**: Flask\[async\] is required because the /process route in app.py is an async def function. Installing this prevents runtime errors.  
2. Update Project Structure for Web UI:  
   Create the following new files and directory within \~/projects/cie-0:  
   * [app.py](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/app.py%5D\(https://github.com/edsblog/cie-0/blob/main/app.py\))  
   * [requirements.txt](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/requirements.txt%5D\(https://github.com/edsblog/cie-0/blob/main/requirements.txt\))  
   * [Dockerfile](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/Dockerfile%5D\(https://github.com/edsblog/cie-0/blob/main/Dockerfile\))  
   * templates/ directory  
     * [templates/index.html](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/templates/index.html%5D\(https://github.com/edsblog/cie-0/blob/main/templates/index.html\))  
3. Create requirements.txt:  
   Populate requirements.txt with all Python dependencies including the web-specific ones.  
   Plaintext  
   google-adk==0.5.0  
   google-cloud-firestore  
   python-dotenv  
   requests  
   beautifulsoup4  
   litellm  
   Flask\[async\]  
   gunicorn

### **Step 5.2: Building the User Interface**

1. **Create templates/index.html**: Populate [templates/index.html](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/templates/index.html%5D\(https://github.com/edsblog/cie-0/blob/main/templates/index.html\)) with HTML, CSS, and JavaScript to create a form for user queries and a display area for the report.  
   * **Special Note on JavaScript**: The JavaScript in this file handles form submission, sends an asynchronous request to the /process backend endpoint, and displays the report or errors.

### **Step 5.3: Backend Logic for CIE Integration (Flask app.py)**

1. **Create app.py**: Populate [app.py](https://www.google.com/search?q=%5Bhttps://github.com/edsblog/cie-0/blob/main/app.py%5D\(https://github.com/edsblog/cie-0/blob/main/app.py\)) with the Flask application code. This script initializes Flask, serves index.html at the root route, and defines an async def process\_query() route at /process to interact with the CoordinatorAgent and return the report as JSON, including error handling.  
   * **Special Note on async def routes**: The async def route enables asynchronous operations with the ADK's Runner.run\_async method.

### **Step 5.4: Preparing for Deployment (Docker)**

1. Create Dockerfile:  
   Create the Dockerfile.  
   * **Special Note on CMD instruction**: The CMD instruction in the Dockerfile must use the shell form (e.g., CMD exec gunicorn ...) or an entrypoint script for the $PORT environment variable to be correctly expanded. The array/exec form (e.g., \["gunicorn", ..., "0.0.0.0:${PORT}", ...\]) might cause Gunicorn to see ${PORT} literally.  
   * **Special Note on Gunicorn Timeout**: Gunicorn's default worker timeout (30 seconds) can be too short for the CIE's processing. Adding \--timeout 180 (or a suitable value) to the gunicorn command in the Dockerfile is crucial for longer-running queries.  
2. Create .dockerignore file:  
   Create the .dockerignore file to exclude unnecessary files (like .venv, \_\_pycache\_\_) from the Docker image, keeping it small and build times faster.

### **Step 5.5: Deploying to Google Cloud Run**

1. Enable Necessary Google Cloud APIs:  
   Ensure Cloud Run API, Artifact Registry API, Cloud Build API, Cloud Firestore API, Google Custom Search API, and Vertex AI API are enabled in your Google Cloud Project.  
2. Authenticate gcloud CLI:  
   Ensure gcloud is authenticated and ADC is set up:  
   Bash  
   gcloud auth login  
   gcloud auth application-default login

   * **Special Note on ADC Quota Project**: The ADC setup must successfully associate with your project as a "quota project." This requires your user account to have the serviceusage.services.use permission (e.g., via the "Service Usage Consumer" role) on the project. Errors like USER\_PROJECT\_DENIED often stem from issues here.  
   * **Special Note on PROJECT\_ID Accuracy**: A typo in PROJECT\_ID can cause significant troubleshooting delays. Meticulously verify environment variables.  
3. Set Up Environment Variables for Deployment:  
   Use a script or set environment variables like PROJECT\_ID, REGION, REPO\_NAME, IMAGE\_NAME. Example:  
   Bash  
   export PROJECT\_ID="your-gcp-project-id"  
   export REGION="your-vertex-ai-region" \# e.g., us-central1  
   export REPO\_NAME="cie-repo"  
   export IMAGE\_NAME="cie-webapp"

4. Create Artifact Registry Repository:  
   If not done, create a Docker repository:  
   Bash  
   gcloud artifacts repositories create ${REPO\_NAME} \\  
       \--repository-format=docker \\  
       \--location=${REGION} \\  
       \--description="CIE Web Application Repository"

5. Configure Docker for Artifact Registry:  
   Authenticate Docker to your Artifact Registry:  
   Bash  
   gcloud auth configure-docker ${REGION}\-docker.pkg.dev

   * **Special Note on Docker CLI**: Ensure Docker CLI is installed and accessible in your WSL environment.  
6. Build and Tag the Docker Image:  
   Navigate to \~/projects/cie-0 and build the image:  
   Bash  
   docker build \-t ${REGION}\-docker.pkg.dev/${PROJECT\_ID}/${REPO\_NAME}/${IMAGE\_NAME}:latest .

   * **Special Note on Image Tagging**: If you change PROJECT\_ID or other variables used in the tag, you must rebuild the image to apply the new tag before pushing. docker push looks for an image with an exact matching local tag.  
7. Push the Docker Image:  
   Push the tagged image:  
   Bash  
   docker push ${REGION}\-docker.pkg.dev/${PROJECT\_ID}/${REPO\_NAME}/${IMAGE\_NAME}:latest

   * **Special Note on Permissions**: Ensure the user account pushing the image has the "Artifact Registry Writer" role (or equivalent) on the project.  
8. Deploy to Cloud Run:  
   Deploy using a command like the following, ensuring API keys are correctly substituted (preferably via a secure method, see "Important Considerations" below):  
   Bash  
   export SERVICE\_NAME="cie-public-ui"  
   gcloud run deploy "${SERVICE\_NAME}" \\  
       \--image="${REGION}\-docker.pkg.dev/${PROJECT\_ID}/${REPO\_NAME}/${IMAGE\_NAME}:latest" \\  
       \--platform="managed" \\  
       \--region="${REGION}" \\  
       \--allow-unauthenticated \\  
       \--set-env-vars="GOOGLE\_CLOUD\_PROJECT=${PROJECT\_ID}" \\  
       \--set-env-vars="GOOGLE\_CLOUD\_LOCATION=${REGION}" \\  
       \--set-env-vars="GOOGLE\_GENAI\_USE\_VERTEXAI=TRUE" \\  
       \--set-env-vars="CUSTOM\_SEARCH\_API\_KEY=YOUR\_ACTUAL\_KEY" \\  
       \--set-env-vars="CUSTOM\_SEARCH\_ENGINE\_ID=YOUR\_ACTUAL\_ID" \\  
       \--memory=2Gi \\  
       \--cpu=1 \\  
       \--project="${PROJECT\_ID}"

   * **Special Note on Cloud Run Resources**: Cloud Run services may need more than default memory (512MiB). Monitor logs for "out of memory" errors and adjust \--memory (e.g., 1Gi, 2Gi) and \--cpu.  
9. **Assign IAM Roles to the Cloud Run Service Account**:  
   * Once deployed, find the service account your Cloud Run service uses (in GCP Console under Cloud Run service details).  
   * Grant this service account these roles:  
     * "Cloud Datastore User" (for Firestore)  
     * "Vertex AI User" (for Vertex AI)

### **Step 5.6: Testing the Deployed Application**

Access the Service URL provided by Cloud Run after successful deployment. Enter a query and verify you receive a report.

* **Special Note on Logs & UI Errors**: Iterative testing and log analysis (Cloud Logging) are key. A UI error like "Unexpected token '\<'" often means a server-side 500 error where HTML (an error page) was returned instead of expected JSON.

## ---

**Important Considerations for Your Deployed Web UI**

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
* **ADK and Async \- Gunicorn Workers**:  
  * app.py uses async def routes. Gunicorn runs with default synchronous workers.  
  * **Recommendation**: For higher concurrency with async Flask, consider an async Gunicorn worker class (e.g., uvicorn.workers.UvicornWorker). This requires adding uvicorn to requirements.txt and modifying the Gunicorn CMD in your Dockerfile.  
* **Cloud Run Service Configuration**:  
  * Adjust concurrency, min/max instances, and CPU allocation as needed.  
* **Cost Management**:  
  * Be mindful of costs for Cloud Run, Artifact Registry, Vertex AI, Custom Search API, and Firestore. Set up budget alerts.  
* **CI/CD (Continuous Integration/Continuous Deployment)**:  
  * For easier updates, consider a CI/CD pipeline using Cloud Build and a source repository.