# This tool will now use the same powerful Vertex AI model as our other components
import vertexai
from vertexai.generative_models import GenerativeModel
from cie_core.config import DEFAULT_AGENT_MODEL

def translate_text(text: str) -> str:
    """Translates classic literary text into modern, easy-to-read English using an AI model."""
    try:
        model = GenerativeModel(DEFAULT_AGENT_MODEL)
        
        # This prompt asks for a change in style, not just literal translation
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
    