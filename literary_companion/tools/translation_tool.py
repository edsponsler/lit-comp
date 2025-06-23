# literary_companion/tools/translation_tool.py

import os
import vertexai
from vertexai.generative_models import GenerativeModel
from cie_core.config import DEFAULT_AGENT_MODEL

# --- THE FIX: Initialize the Vertex AI library ---
# This tells the tool which Google Cloud project and region to use.
try:
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
    REGION = "us-central1" # Or your preferred region
    vertexai.init(project=PROJECT_ID, location=REGION)
except Exception as e:
    print(f"--- CRITICAL: Failed to initialize Vertex AI in translation_tool. {e} ---")
# -------------------------------------------------


def translate_text(text: str) -> str:
    """Translates classic literary text into modern, easy-to-read English using an AI model."""
    try:
        model = GenerativeModel(DEFAULT_AGENT_MODEL)
        
        prompt = (
            "You are a helpful translation assistant. Your task is to rephrase the following "
            "passage from a classic novel into clear, modern, and easily understandable English. "
            "Preserve the original meaning, characters, and events exactly. Only update the "
            "vocabulary, sentence structure, and tone to be more contemporary. Do not add any "
            "commentary or introductions.\n\n"
            f"CLASSIC TEXT:\n---\n{text}\n---\n\nMODERN TRANSLATION:"
        )
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"--- Tool: Error during AI translation: {e} ---")
        return f"Error: Translation failed. {e}"