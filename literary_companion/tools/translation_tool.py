# literary_companion/tools/translation_tool.py

from vertexai.generative_models import GenerativeModel
from literary_companion.config import DEFAULT_AGENT_MODEL

def generate_content_with_prompt(prompt: str) -> str:
    """
    A generic function to generate content from a given prompt using a generative AI model.
    """
    try:
        model = GenerativeModel(DEFAULT_AGENT_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"--- Tool: Error during AI content generation: {e} ---")
        return f"Error: AI content generation failed. {e}"

def translate_text(text: str) -> str:
    """Translates classic literary text into modern, easy-to-read English using an AI model."""
    
    prompt = (
        "You are a helpful translation assistant. Your task is to rephrase the following "
        "passage from a classic novel into clear, modern, and easily understandable English. "
        "Preserve the original meaning, characters, and events exactly. Only update the "
        "vocabulary, sentence structure, and tone to be more contemporary. Do not add any "
        "commentary or introductions.\n\n"
        f"CLASSIC TEXT:\n---\n{text}\n---\n\nMODERN TRANSLATION:"
    )
    
    return generate_content_with_prompt(prompt)