# literary_companion/tools/translation_tool.py

from google.cloud import translate_v2 as translate
from google.adk.tools import FunctionTool

def translate_text(text: str, target_language: str = 'en-US') -> str:
    """Translates a body of text using Google Cloud Translation API."""
    try:
        translate_client = translate.Client()
        result = translate_client.translate(text, target_language=target_language)
        translated_text = result['translatedText']
        print(f"--- Tool: Successfully translated {len(text)} chars ---")
        return translated_text
    except Exception as e:
        print(f"--- Tool: Error during translation: {e} ---")
        return f"Error: Translation failed. {e}"

# Expose the function as an ADK FunctionTool
translation_tool = FunctionTool(translate_text)