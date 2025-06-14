# literary_companion/tools/gcs_tool.py
import json
import re
from google.cloud import storage
from google.adk.tools import FunctionTool
from literary_companion.tools.translation_tool import translate_text

def read_text_from_gcs(bucket_name: str, file_name: str) -> str:
    """Reads a text file from a GCS bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        content = blob.download_as_text()
        print(f"--- Tool: Successfully read {len(content)} chars from gs://{bucket_name}/{file_name} ---")
        return content
    except Exception as e:
        print(f"--- Tool: Error reading from GCS: {e} ---")
        return f"Error: Could not read file from GCS. {e}"

def write_text_to_gcs(bucket_name: str, file_name: str, content: str) -> str:
    """Writes text content to a file in a GCS bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        blob.upload_from_string(content)
        print(f"--- Tool: Successfully wrote to gs://{bucket_name}/{file_name} ---")
        return f"Success: Content written to gs://{bucket_name}/{file_name}"
    except Exception as e:
        print(f"--- Tool: Error writing to GCS: {e} ---")
        return f"Error: Could not write file to GCS. {e}"

def process_and_translate_book(bucket_name: str, file_name: str) -> str:
    """
    Reads a book from GCS, translates it paragraph by paragraph,
    and writes the structured result back to GCS. This is a complete workflow.
    """
    print("--- Master Tool: Starting book processing workflow. ---")
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        original_content = blob.download_as_text()
        print(f"--- Master Tool: Successfully read {len(original_content)} chars.")
    except Exception as e:
        return f"Error: Failed to read source file. {e}"

    # 1. Split the entire text by double newlines to get paragraph blocks.
    # This pattern splits on two or more consecutive newline characters,
    # handling both Linux (\n) and Windows (\r\n) style endings robustly.
    paragraph_blocks = re.split(r'(?:\r\n|\n){2,}', original_content.strip())

    prepared_paragraphs = []
    print(f"--- Master Tool: Segmented text into {len(paragraph_blocks)} paragraphs. ---")

    for i, p_block in enumerate(paragraph_blocks):
        # Clean up any remaining single newlines within the paragraph
        cleaned_paragraph = p_block.replace('\n', ' ').replace('\r', ' ').strip()

        if not cleaned_paragraph:
            continue

        paragraph_id = f"p-{i+1}"
        print(f"--- Master Tool: Translating {paragraph_id} ({len(cleaned_paragraph)} chars)... ---")
        
        # 3. Translate the clean, complete paragraph.
        translated_p_text = translate_text(cleaned_paragraph)
        
        if translated_p_text.startswith("Error:"):
             print(f"--- Master Tool: Skipping paragraph {paragraph_id} due to translation error. ---")
             continue

        prepared_paragraphs.append({
            "paragraph_id": paragraph_id,
            "original_text": cleaned_paragraph, # Store the cleaned version
            "translated_text": translated_p_text
        })
    
    final_output_obj = {"paragraphs": prepared_paragraphs}
    final_output_json = json.dumps(final_output_obj, indent=2)

    output_filename = file_name.replace('.txt', '_prepared.json')
    try:
        output_blob = bucket.blob(output_filename)
        output_blob.upload_from_string(final_output_json, content_type='application/json')
        result_message = f"Success! Processed book and saved to gs://{bucket_name}/{output_filename}"
        print(f"--- Master Tool: {result_message} ---")
        return result_message
    except Exception as e:
        return f"Error: Failed to write prepared file to GCS. {e}"

# Expose the functions as ADK FunctionTools
gcs_reader_tool = FunctionTool(read_text_from_gcs)
gcs_writer_tool = FunctionTool(write_text_to_gcs)
book_processor_tool = FunctionTool(process_and_translate_book)