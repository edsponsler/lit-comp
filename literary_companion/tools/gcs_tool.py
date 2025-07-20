# literary_companion/tools/gcs_tool.py
import json
import logging
import re
from google.cloud import storage
import tempfile
import time
from datetime import datetime
from typing import List, Optional
from google.adk.tools import FunctionTool
import concurrent.futures
from literary_companion.tools.translation_tool import translate_text

# Configure logging for structured output that integrates well with Cloud Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a single, module-level client instance for reuse.
# The client will be initialized once when the module is first imported.
try:
    storage_client = storage.Client()
except Exception as e:
    logging.critical(f"Failed to initialize GCS client: {e}", exc_info=True)
    storage_client = None

def read_text_from_gcs(bucket_name: str, file_name: str) -> str:
    """Reads a text file from a GCS bucket."""
    if not storage_client:
        # Raise an exception for unrecoverable errors.
        raise ConnectionError("GCS client not initialized.")
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        content = blob.download_as_text()
        logging.info(f"Successfully read {len(content)} chars from gs://{bucket_name}/{file_name}")
        return content
    except Exception as e: # Catches GCS-specific errors like google.api_core.exceptions.NotFound
        logging.error(f"Error reading from GCS: {e}", exc_info=True)
        # Re-raise the exception to be handled by the caller.
        # This is more idiomatic than returning an error string.
        raise IOError(f"Could not read gs://{bucket_name}/{file_name}") from e

def write_text_to_gcs(bucket_name: str, file_name: str, content: str) -> str:
    """Writes text content to a file in a GCS bucket."""
    if not storage_client:
        return "Error: GCS client not initialized."
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        blob.upload_from_string(content)
        logging.info(f"Successfully wrote to gs://{bucket_name}/{file_name}")
        return f"Success: Content written to gs://{bucket_name}/{file_name}"
    except Exception as e:
        logging.error(f"Error writing to GCS: {e}", exc_info=True)
        return f"Error: Could not write file to GCS. {e}"

def _translate_paragraph_worker(paragraph_id: int, paragraph_text: str) -> Optional[dict]:
    """
    Worker function to translate a single paragraph.
    Designed to be called from a ThreadPoolExecutor.
    """
    if not paragraph_text:
        return None

    translated_text = translate_text(paragraph_text)

    if translated_text.startswith("Error:"):
        logging.warning(f"Skipping p-{paragraph_id} due to translation error.")
        return None

    # This is the success log you requested for each paragraph.
    logging.info(f"Successfully translated p-{paragraph_id}.")

    return {
        "paragraph_id": f"p-{paragraph_id}",
        "original_text": paragraph_text,
        "translated_text": translated_text,
    }

def process_and_translate_book(bucket_name: str, file_name: str) -> str:
    """
    Reads a book from GCS, translates it paragraph by paragraph in parallel,
    and writes the structured result back to GCS. This is a complete workflow.
    """
    logging.info("Starting book processing workflow.")
    if not storage_client:
        return "Error: GCS client not initialized."
    start_time = time.monotonic()
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        original_content = blob.download_as_text()
        logging.info(f"Successfully read {len(original_content)} chars.")
    except Exception as e:
        return f"Error: Failed to read source file. {e}"

    # 1. Split the entire text by double newlines to get paragraph blocks.
    # This pattern splits on two or more consecutive newline characters,
    # handling both Linux (\n) and Windows (\r\n) style endings robustly.
    paragraph_blocks = re.split(r'(?:\r\n|\n){2,}', original_content.strip())

    total_paragraphs = len(paragraph_blocks)
    logging.info(f"Segmented text into {total_paragraphs} paragraphs. Starting parallel translation...")

    # Use a list of the correct size to store results in order, preventing race conditions.
    # By explicitly typing the list, we inform the linter what types are expected.
    prepared_paragraphs: List[Optional[dict]] = [None] * total_paragraphs

    # Use a ThreadPoolExecutor to run translations in parallel.
    # max_workers can be tuned, but 16 is a reasonable starting point for I/O-bound tasks.
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        future_to_index = {
            executor.submit(_translate_paragraph_worker, i + 1, p_block.replace('\n', ' ').replace('\r', ' ').strip()): i
            for i, p_block in enumerate(paragraph_blocks)
        }

        processed_count = 0
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                if result:
                    prepared_paragraphs[index] = result
            except Exception as exc:
                logging.error(f"Paragraph index {index} generated an exception: {exc}", exc_info=True)
            
            processed_count += 1
            if processed_count % 50 == 0 or processed_count == total_paragraphs:
                percentage_complete = (processed_count / total_paragraphs) * 100
                logging.info(f"Progress - Completed translation for {processed_count} of {total_paragraphs} paragraphs ({percentage_complete:.2f}% complete).")

    # Filter out any None results from failed translations or empty paragraphs
    final_paragraphs = [p for p in prepared_paragraphs if p is not None]

    output_filename = file_name.replace('.txt', '_prepared.json')
    
    # Use a temporary file on the build worker's local disk to build the JSON.
    # This is highly memory-efficient for large files.
    try:
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=True) as tmp_file:
            tmp_file.write('{\n  "paragraphs": [\n')
            is_first_paragraph = True
            for paragraph_data in final_paragraphs:
                if not is_first_paragraph:
                    tmp_file.write(',\n')
                json.dump(paragraph_data, tmp_file, indent=4)
                is_first_paragraph = False

            tmp_file.write('\n  ]\n}\n')
            # Rewind the file to the beginning to be read for upload
            tmp_file.seek(0)
            # Upload the contents of the temporary file to GCS
            output_blob = bucket.blob(output_filename)
            output_blob.upload_from_file(tmp_file, content_type='application/json')
            end_time = time.monotonic()
            duration_minutes = (end_time - start_time) / 60
            result_message = (
                f"Success! Processed {len(final_paragraphs)} paragraphs and saved to gs://{bucket_name}/{output_filename}. "
                f"Total time: {duration_minutes:.2f} minutes."
            )
            logging.info(result_message)
            return result_message
    except Exception as e:
        logging.error(f"Failed to write prepared file to GCS: {e}", exc_info=True)
        return f"Error: Failed to write prepared file to GCS. {e}"

# Expose the functions as ADK FunctionTools
gcs_reader_tool = FunctionTool(read_text_from_gcs)
gcs_writer_tool = FunctionTool(write_text_to_gcs)
book_processor_tool = FunctionTool(process_and_translate_book)