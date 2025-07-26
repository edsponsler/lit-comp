
# In literary_companion/tools/screenplay_v2_tool.py
import json
from google.cloud import storage

def get_novel_text_for_chapters(bucket_name: str, file_name: str, chapters_to_process: str) -> str:
    """Reads the prepared novel from GCS and returns the text for the specified chapters.

    Args:
        bucket_name: The GCS bucket where the prepared novel is stored.
        file_name: The name of the prepared novel JSON file (e.g., 'moby_dick_prepared.json').
        chapters_to_process: A string describing the chapters to include (e.g., "Chapters 1 through 16").

    Returns:
        The text of the specified chapters.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    try:
        json_content = blob.download_as_text()
        data = json.loads(json_content)
        paragraphs = data.get("paragraphs", [])

        # This is a simple example of how you might filter by chapter.
        # A more robust implementation would parse the 'chapters_to_process' string.
        # For now, we'll just use all the text.
        modern_novel_text = " ".join(p.get("translated_text", "") for p in paragraphs if p.get("translated_text"))
        if not modern_novel_text:
            return "Error: Could not find any translated text in the prepared file."
        return modern_novel_text
    except Exception as e:
        return f"Error reading or parsing prepared file: {e}"
