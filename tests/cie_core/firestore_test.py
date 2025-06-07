# tests/cie_core/firestore_test.py
from google.cloud import firestore
import os

# Use python-dotenv to load .env variables
from dotenv import load_dotenv
load_dotenv() # Call this before accessing os.getenv if .env isn't auto-loaded

def check_firestore_connection():
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if project_id:
            print(f"Attempting to connect to Firestore in project: {project_id}")
            db = firestore.Client(project=project_id)
        else:
            print("Attempting to connect to Firestore (project ID not specified, relying on ADC default or gcloud config)")
            db = firestore.Client()

        doc_ref = db.collection("test_connection_collection").document("test_doc")
        print(f"Successfully initialized Firestore client. Document reference: {doc_ref.path}")
        print("Firestore setup appears to be working!")
        print("You are ready to proceed with 'Building CIE Tutorial Part 1' and implement the StatusBoardTool.")

    except Exception as e:
        print(f"Error initializing Firestore client: {e}")
        print("Please check the following:")
        print("1. Google Cloud Project ID is correct (set via GOOGLE_CLOUD_PROJECT in .env or gcloud config).")
        print("2. Firestore API is enabled in your Google Cloud project.")
        print("3. You are authenticated (gcloud auth login and gcloud auth application-default login in WSL).")
        print("4. The google-cloud-firestore library is installed in your WSL virtual environment.")

if __name__ == "__main__":
    check_firestore_connection()
